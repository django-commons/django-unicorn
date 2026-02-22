import logging
from datetime import timedelta
from decimal import Decimal
from functools import lru_cache
from types import MappingProxyType
from typing import Any

import orjson
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import (
    DateField,
    DateTimeField,
    DurationField,
    Model,
    QuerySet,
    TimeField,
)
from django.utils.dateparse import (
    parse_date,
    parse_datetime,
    parse_duration,
    parse_time,
)
from django.utils.duration import duration_string

from django_unicorn.utils import is_int, is_non_string_sequence

try:
    from pydantic import BaseModel as PydanticBaseModel
except ImportError:
    PydanticBaseModel = None  # type: ignore


logger = logging.getLogger(__name__)

django_json_encoder = DjangoJSONEncoder()


class JSONDecodeError(Exception):
    pass


class InvalidFieldNameError(Exception):
    def __init__(self, field_name: str, data: dict | None = None):
        message = f"Cannot resolve '{field_name}'."

        if data:
            available = ", ".join(data.keys())
            message = f"{message} Choices are: {available}"

        super().__init__(message)


class InvalidFieldAttributeError(Exception):
    def __init__(self, field_name: str, field_attr: str, data: dict | None = None):
        message = f"Cannot resolve '{field_attr}'."

        if data:
            available = ", ".join(data[field_name].keys())
            message = f"{message} Choices on '{field_name}' are: {available}"

        super().__init__(message)


def _parse_field_values_from_string(model: Model) -> None:
    """
    Convert the model fields' value to match the field type if appropriate.

    This is mostly to deal with field string values that will get saved as a date-related field.
    """

    for field in model._meta.fields:
        val = getattr(model, field.attname)

        if not isinstance(val, str):
            continue

        if isinstance(field, DateTimeField):
            setattr(model, field.attname, parse_datetime(val))
        elif isinstance(field, TimeField):
            setattr(model, field.attname, parse_time(val))
        elif isinstance(field, DateField):
            setattr(model, field.attname, parse_date(val))
        elif isinstance(field, DurationField):
            setattr(model, field.attname, parse_duration(val))


def _get_many_to_many_field_related_names(model: Model) -> list[str]:
    """
    Get the many-to-many fields for a particular model. Returns either the automatically
    defined field name (i.e. something_set) or the related name.
    """

    # Use this internal method so that the fields can be cached
    @lru_cache(maxsize=128, typed=True)
    def _get_many_to_many_field_related_names_from_meta(meta):
        names = []

        for field in meta.get_fields():
            if field.is_relation and field.many_to_many:
                related_name = field.name

                if field.auto_created:
                    related_name = field.related_name or f"{field.name}_set"

                names.append(related_name)

        return names

    return _get_many_to_many_field_related_names_from_meta(model._meta)


def _get_m2m_field_serialized(model: Model, field_name) -> list:
    pks = []

    try:
        related_descriptor = getattr(model, field_name)

        # Get `pk` from `all` because it will re-use the cached data if the m-2-m field is prefetched
        # Using `values_list("pk", flat=True)` or `only()` won't use the cached prefetched values
        pks = [m.pk for m in related_descriptor.all()]
    except ValueError:
        # ValueError is thrown when the model doesn't have an id already set
        pass

    return pks


def _handle_inherited_models(model: Model, model_json: dict):
    """
    Handle if the model has a parent (i.e. the model is a subclass of another model).

    Subclassed model's fields don't get serialized
    (https://docs.djangoproject.com/en/stable/topics/serialization/#inherited-models)
    so those fields need to be retrieved manually.
    """

    if model._meta.get_parent_list():
        for field in model._meta.get_fields():
            if field.name not in model_json and hasattr(field, "primary_key") and not field.primary_key:
                if field.is_relation:
                    # We already serialized the m2m fields above, so we can skip them, but need to handle FKs
                    if not field.many_to_many:
                        foreign_key_field = getattr(model, field.name)
                        foreign_key_field_pk = getattr(
                            foreign_key_field,
                            "pk",
                            getattr(foreign_key_field, "id", None),
                        )
                        model_json[field.name] = foreign_key_field_pk
                else:
                    value = getattr(model, field.name)

                    # Explicitly handle `timedelta`, but use the DjangoJSONEncoder for everything else
                    if isinstance(value, timedelta):
                        value = duration_string(value)
                    else:
                        # Make sure the value is properly serialized
                        value = django_json_encoder.encode(value)

                        # The DjangoJSONEncoder has extra double-quotes for strings so remove them
                        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]

                    model_json[field.name] = value


def _get_model_dict(model: Model) -> dict:
    """
    Serializes Django models. Uses the built-in Django JSON serializer, but moves the data around to
    remove some unnecessary information and make the structure more compact.
    """

    _parse_field_values_from_string(model)

    # Django's `serialize` method always returns a string of an array
    serialized_model = serialize("json", [model])

    try:
        # Django's `serialize` method always returns a string of an array,
        # so remove the brackets from the resulting string
        model_json = orjson.loads(serialized_model[1:-1])
    except orjson.JSONDecodeError:
        # Convert the string into a dictionary and grab the `pk`
        model_json = orjson.loads(serialized_model)[0]
    model_pk = model_json.get("pk")

    # Shuffle around the serialized pieces to condense the size of the payload
    model_json = model_json.get("fields")
    model_json["pk"] = model_pk

    # Set `pk` for models that subclass another model which only have `id` set
    if not model_pk:
        model_json["pk"] = model.pk or model.id  # type: ignore

    # Add in m2m fields
    m2m_field_names = _get_many_to_many_field_related_names(model)

    for m2m_field_name in m2m_field_names:
        model_json[m2m_field_name] = _get_m2m_field_serialized(model, m2m_field_name)

    _handle_inherited_models(model, model_json)

    return model_json


def _json_serializer(obj):
    """
    Handle the objects that the `orjson` deserializer can't handle automatically.

    The types handled by `orjson` by default: dataclass, datetime, enum, float, int, numpy, str, uuid.
    The types handled in this class: Django Model, Django QuerySet, Decimal, or any object with `to_json` method.

    TODO: Investigate other ways to serialize objects automatically.
    e.g. Using DRF serializer: https://www.django-rest-framework.org/api-guide/serializers/#serializing-objects
    """
    from django_unicorn.components import UnicornView  # noqa: PLC0415

    try:
        if isinstance(obj, UnicornView):
            return {
                "name": obj.component_name,
                "id": obj.component_id,
                "key": obj.component_key,
            }
        elif isinstance(obj, Model):
            return _get_model_dict(obj)
        elif isinstance(obj, QuerySet):
            queryset_json = []

            for model in obj:
                if obj.query.values_select and isinstance(model, dict):
                    # If the queryset was created with values it's already a dictionary
                    model_json = model
                else:
                    model_json = _get_model_dict(model)

                queryset_json.append(model_json)

            return queryset_json
        elif PydanticBaseModel and isinstance(obj, PydanticBaseModel):  # type: ignore
            return obj.dict()
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, MappingProxyType):
            # Return a regular dict for `mappingproxy`
            return obj.copy()
        elif hasattr(obj, "to_json"):
            return obj.to_json()
    except Exception as e:
        # Log this because the `TypeError` and resulting stacktrace lacks context
        logger.exception(e)

    raise TypeError


def _fix_floats(current: dict, data: dict | None = None, paths: list | None = None) -> None:
    """
    Recursively change any Python floats to a string so that JavaScript
    won't convert the float to an integer when deserializing.

    Params:
        current: Dictionary in which to check for and fix floats.
    """

    if data is None:
        data = current

    if paths is None:
        paths = []

    if isinstance(current, dict):
        for key, val in current.items():
            paths.append(key)
            _fix_floats(val, data, paths=paths)
            paths.pop()
    elif isinstance(current, (list, tuple)):
        if isinstance(current, tuple) and paths:
            # Tuples are immutable; convert to list in the parent container so
            # we can mutate float values inside it.
            _piece = data
            for idx, path in enumerate(paths):
                if idx == len(paths) - 1:
                    _piece[path] = list(current)
                else:
                    _piece = _piece[path]
            current = _piece[paths[-1]]
        for idx, item in enumerate(current):
            paths.append(idx)
            _fix_floats(item, data, paths=paths)
            paths.pop()
    elif isinstance(current, float):
        _piece = data

        for idx, path in enumerate(paths):
            if idx == len(paths) - 1:
                # `path` can be a dictionary key or list index,
                # but in either instance it is set the same way
                _piece[path] = str(current)
            else:
                _piece = _piece[path]


def _sort_dict(data: dict) -> dict:
    """
    Recursively sort the dictionary keys so that JavaScript won't change the order
    and change the generated checksum.

    Params:
        data: Dictionary to sort.
    """

    if not isinstance(data, dict):
        return data

    items = [
        [k, v]
        for k, v in sorted(
            data.items(),
            key=lambda item: item[0] if not is_int(item[0]) else int(item[0]),
        )
    ]

    for item in items:
        if isinstance(item[1], dict):
            item[1] = _sort_dict(item[1])

    return dict(items)


def _exclude_field_attributes(dict_data: dict[Any, Any], exclude_field_attributes: tuple[str] | None = None) -> None:
    """
    Remove the field attribute from `dict_data`. Handles nested attributes with a dot.

    Example:
    _exclude_field_attributes({"1": {"2": {"3": "4"}}}, ("1.2.3",)) == {"1": {"2": {}}}
    """

    if exclude_field_attributes:
        for field in exclude_field_attributes:
            field_splits = field.split(".")
            nested_attribute_split_count = 2

            if len(field_splits) > nested_attribute_split_count:
                next_attribute_index = field.index(".") + 1
                remaining_field_attributes = field[next_attribute_index:]
                remaining_dict_data = dict_data[field_splits[0]]

                return _exclude_field_attributes(remaining_dict_data, (remaining_field_attributes,))
            elif len(field_splits) == nested_attribute_split_count:
                (field_name, field_attr) = field_splits

                if field_name not in dict_data:
                    raise InvalidFieldNameError(field_name=field_name, data=dict_data)

                if dict_data[field_name] is not None:
                    if field_attr not in dict_data[field_name]:
                        raise InvalidFieldAttributeError(field_name=field_name, field_attr=field_attr, data=dict_data)

                    del dict_data[field_name][field_attr]


@lru_cache(maxsize=128, typed=True)
def _dumps(
    serialized_data: bytes,
    *,
    fix_floats: bool = True,
    exclude_field_attributes: tuple[str] | None = None,
    sort_dict: bool = True,
) -> dict:
    """
    Dump serialized data with custom massaging.

    Features:
       - fix floats
       - remove specific keys as needed
       - sort dictionary
    """

    data = orjson.loads(serialized_data)

    if fix_floats:
        _fix_floats(data)

    if exclude_field_attributes:
        # Excluding field attributes needs to de-serialize and then serialize again to
        # handle complex objects
        _exclude_field_attributes(data, exclude_field_attributes)

    if sort_dict:
        # Sort dictionary manually because stringified integers don't get sorted
        # correctly with `orjson.OPT_SORT_KEYS` and JavaScript will sort the keys
        # as if they are integers
        data = _sort_dict(data)

    return data


def dumps(
    data: Any,
    *,
    fix_floats: bool = True,
    exclude_field_attributes: tuple[str, ...] | None = None,
    sort_dict: bool = True,
) -> str:
    """
    Converts the passed-in dictionary to a string representation.

    Handles the following objects: dataclass, datetime, enum, float, int, numpy, str, uuid,
    Django Model, Django QuerySet, Pydantic models (`PydanticBaseModel`), any object with `to_json` method.

    Args:
        param fix_floats: Whether any floats should be converted to strings. Defaults to `True`,
            but will be faster without it.
        param exclude_field_attributes: Tuple of strings with field attributes to remove, i.e. "1.2"
            to remove the key `2` from `{"1": {"2": "3"}}`
        param sort_dict: Whether the `dict` should be sorted. Defaults to `True`, but
            will be faster without it.

    Returns a `str` instead of `bytes` (which deviates from `orjson.dumps`), but seems more useful.
    """

    if exclude_field_attributes is not None and not is_non_string_sequence(exclude_field_attributes):
        raise AssertionError("exclude_field_attributes type needs to be a sequence")

    # Call `dumps` to make sure that complex objects are serialized correctly
    serialized_data = orjson.dumps(data, default=_json_serializer)

    data = _dumps(
        serialized_data,
        fix_floats=fix_floats,
        exclude_field_attributes=exclude_field_attributes,
        sort_dict=sort_dict,
    )

    serialized_data = orjson.dumps(data)

    return serialized_data.decode("utf-8")


def loads(string: str) -> dict:
    """
    Converts a string representation to dictionary.
    """

    try:
        return orjson.loads(string)
    except orjson.JSONDecodeError as e:
        raise JSONDecodeError from e


def model_value(model: Model, *fields: str):
    """
    Serializes a model into a dictionary with the fields as specified in the `fields` argument.
    """

    model_data = {}
    model_dict = _get_model_dict(model)

    if not fields:
        return model_dict

    for field in fields:
        if field in model_dict:
            model_data[field] = model_dict[field]

    return model_data
