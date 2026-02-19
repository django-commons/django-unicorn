import inspect
import logging
from dataclasses import is_dataclass
from datetime import date, datetime, time, timedelta, timezone
from inspect import signature
from typing import Any, Union

try:
    from types import UnionType
except ImportError:
    UnionType = Union  # type: ignore

from typing import get_type_hints as typing_get_type_hints
from uuid import UUID

try:
    from pydantic import BaseModel

    def _check_pydantic(cls) -> bool:
        return issubclass(cls, BaseModel)

except ImportError:

    def _check_pydantic(cls) -> bool:  # noqa: ARG001
        return False


from django.db.models import Model, QuerySet
from django.utils.dateparse import (
    parse_date,
    parse_datetime,
    parse_duration,
    parse_time,
)

from django_unicorn.typing import QuerySetType

try:
    from typing import get_args, get_origin
except ImportError:
    # Fallback to dunder methods for older versions of Python
    def get_args(tp: Any) -> tuple[Any, ...]:
        if hasattr(tp, "__args__"):
            return tp.__args__
        return ()

    def get_origin(tp: Any) -> Any | None:
        if hasattr(tp, "__origin__"):
            return tp.__origin__
        return None


try:
    from cachetools.lru import LRUCache  # type: ignore
except ImportError:
    from cachetools import LRUCache


logger = logging.getLogger(__name__)

type_hints_cache = LRUCache(maxsize=100)
function_signature_cache = LRUCache(maxsize=100)


def _parse_bool(value):
    return str(value) == "True"


# Functions that attempt to convert something that failed while being parsed by
# `ast.literal_eval`.
CASTERS = {
    datetime: parse_datetime,
    time: parse_time,
    date: parse_date,
    timedelta: parse_duration,
    UUID: UUID,
    bool: _parse_bool,
}


def get_type_hints(obj) -> dict:
    """Get type hints from an object. These get cached in a local memory cache for quicker look-up later.

    Returns:
        An empty dictionary if no type hints can be retrieved.
    """

    type_hints = {}

    try:
        if obj in type_hints_cache:
            return type_hints_cache[obj]
    except TypeError:
        # Ignore issues with checking for an object in the cache, e.g. when a Django model is missing a PK
        pass

    try:
        if inspect.isclass(obj) or inspect.ismodule(obj) or inspect.isroutine(obj):
            type_hints = typing_get_type_hints(obj)
        elif hasattr(obj, "__class__"):
            # Should be called with class object (instead of instance) to get type hints of parent classes. From docs:
            # "If obj is a class C, the function returns a dictionary that merges annotations from C's base classes with
            # those on C directly. This is done by traversing C.__mro__ and iteratively combining __annotations__
            # dictionaries." (https://docs.python.org/3/library/typing.html#typing.get_type_hints)
            type_hints = typing_get_type_hints(obj.__class__)
        else:
            type_hints = typing_get_type_hints(obj)
    except (TypeError, NameError):
        # Fallback to __annotations__ if get_type_hints fails, which can happen in some environments
        # (e.g. Python 3.11 with coverage instrumentation)
        type_hints = getattr(obj, "__annotations__", {})

    try:
        # Cache the type hints just in case
        type_hints_cache[obj] = type_hints
    except TypeError:
        pass

    return type_hints


def cast_value(type_hint, value):
    """Try to cast the value based on the type hint and
    `django_unicorn.call_method_parser.CASTERS`.

    Additional features:
    - convert `int`/`float` epoch to `datetime` or `date`
    - instantiate the `type_hint` class with passed-in value
    """

    type_hints = []

    if get_origin(type_hint) is Union or get_origin(type_hint) is UnionType or get_origin(type_hint) is list:
        for arg in get_args(type_hint):
            type_hints.append(arg)
    else:
        type_hints.append(type_hint)

    if get_origin(type_hint) is list:
        if len(type_hints) == 1:
            # There should only be one argument for a list type hint
            arg = type_hints[0]

            # Handle type hints that are a list by looping over the value and
            # casting each item individually
            return [cast_value(arg, item) for item in value]

    if get_origin(type_hint) is tuple:
        type_args = get_args(type_hint)
        if len(type_args) == 1:
            # Homogeneous tuple hint like tuple[dict[str, float|str]] —
            # the single arg applies to every element
            arg = type_args[0]
            return tuple(cast_value(arg, item) for item in value)
        elif len(type_args) >= 2 and type_args[-1] is not Ellipsis:
            # Fixed-length heterogeneous tuple: tuple[str, int, float]
            return tuple(cast_value(t, item) for t, item in zip(type_args, value))

    if get_origin(type_hint) is dict:
        type_args = get_args(type_hint)
        if len(type_args) == 2 and isinstance(value, dict):
            # dict[K, V] — cast each value to the V type so that e.g.
            # dict[str, float|str] converts string "3.4" back to float 3.4
            value_type = type_args[1]
            return {k: cast_value(value_type, v) for k, v in value.items()}

    # Handle Optional type hint and the value is None
    if type(None) in type_hints and value is None:
        return value

    for _type_hint in type_hints:
        if _type_hint == type(None):  # noqa: E721
            continue

        caster = CASTERS.get(_type_hint)

        if caster:
            try:
                value = caster(value)
                break
            except TypeError:
                if (_type_hint is datetime or _type_hint is date) and (isinstance(value, float | int)):
                    try:
                        value = datetime.fromtimestamp(value, tz=timezone.utc)

                        if _type_hint is date:
                            value = value.date()

                        break
                    except ValueError:
                        pass
        else:
            if isinstance(_type_hint, type) and issubclass(_type_hint, Model):
                continue

            if _check_pydantic(_type_hint) or is_dataclass(_type_hint):
                value = _type_hint(**value)
                break

            try:
                value = _type_hint(value)
                break
            except ValueError:
                # float("abc") raises ValueError; continue to the next type in a
                # Union (e.g. the `str` in float|str) before giving up.
                continue

    return value


def cast_attribute_value(obj, name, value):
    """Try to cast the value of an object's attribute based on the type hint."""

    type_hints = get_type_hints(obj)
    type_hint = type_hints.get(name)

    if type_hint:
        if is_queryset(obj, type_hint, value):
            # Do not try to cast the queryset here
            pass
        elif not is_dataclass(type_hint):
            try:
                value = cast_value(type_hint, value)
            except TypeError:
                # Ignore this exception because some type-hints can't be instantiated like this (e.g. `List[]`)
                pass

    return value


def get_method_arguments(func) -> list[str]:
    """Gets the arguments for a method.

    Returns:
        A list of strings, one for each argument.
    """

    if func in function_signature_cache:
        return function_signature_cache[func]

    function_signature = signature(func)
    function_signature_cache[func] = list(function_signature.parameters)

    return function_signature_cache[func]


def is_queryset(obj, type_hint, value):
    """Determines whether an obj is a `QuerySet` or not based on the current instance of the
    component or the type hint."""

    is_queryset_type = False

    if type_hint:
        if get_origin(type_hint) is QuerySetType:
            is_queryset_type = True
        elif get_origin(type_hint) is Union or get_origin(type_hint) is UnionType:
            for arg in get_args(type_hint):
                if get_origin(arg) is QuerySetType:
                    is_queryset_type = True
                    break

    return ((isinstance(obj, QuerySet) or is_queryset_type) and isinstance(value, list)) or isinstance(value, QuerySet)


def _construct_model(model_type, model_data: dict):
    """Construct a model based on the type and dictionary data."""

    if not model_data:
        return None

    model = model_type()

    for field_name, field_value in model_data.items():
        for field in model._meta.fields:
            if field.name == field_name or (field_name == "pk" and field.primary_key):
                column_name = field.name

                if field.is_relation:
                    column_name = field.attname

                setattr(model, column_name, field_value)

                break

    return model


def create_queryset(obj, type_hint, value) -> QuerySet:
    """Create a queryset based on the `value`. If needed, the queryset will be created based on the `QuerySetType`.

    For example, all of these ways fields are equivalent:

    class TestComponent(UnicornView):
        queryset_with_empty_list: QuerySetType[SomeModel] = []
        queryset_with_none: QuerySetType[SomeModel] = None
        queryset_with_empty_queryset: QuerySetType[SomeModel] = SomeModel.objects.none()
        queryset_with_no_typehint = SomeModel.objects.none()

    Params:
        obj: Object.
        type_hint: The optional type hint for the field.
        value: JSON.
    """

    # Get original queryset, update it with dictionary data and then
    # re-set the queryset; this is required because otherwise the
    # property changes type from a queryset to the serialized queryset
    # (which is an array of dictionaries)
    queryset = obj
    model_type = None

    if type_hint and not isinstance(queryset, QuerySet):
        if get_origin(type_hint) is Union or get_origin(type_hint) is UnionType:
            for arg in get_args(type_hint):
                if get_origin(arg) is QuerySetType:
                    type_arguments = get_args(arg)
                    if type_arguments:
                        if hasattr(type_arguments[0], "objects"):
                            queryset = type_arguments[0].objects.none()
                            model_type = type_arguments[0]
                    break
        else:
            type_arguments = get_args(type_hint)

            if type_arguments:
                # First type argument should be the type of the model
                if hasattr(type_arguments[0], "objects"):
                    queryset = type_arguments[0].objects.none()
                    model_type = type_arguments[0]

    if not model_type and not isinstance(queryset, QuerySet):
        raise Exception(f"Getting Django Model type failed for type: {type(queryset)}")

    if not model_type:
        # Assume that `queryset` is _actually_ a QuerySet so grab the
        # `model` attribute in that case
        model_type = queryset.model

    for model_value in value:
        model_found = False

        # The following portion uses the internal `_result_cache` QuerySet API which
        # is private and could potentially change in the future, but not sure how
        # else to change internal models or append a new model to a QuerySet (probably
        # because it isn't really allowed)
        if queryset._result_cache is None:
            # Explicitly set `_result_cache` to an empty list
            queryset._result_cache = []

        for idx, model in enumerate(queryset._result_cache):
            if hasattr(model, "pk") and model.pk == model_value.get("pk"):
                constructed_model = _construct_model(model_type, model_value)
                queryset._result_cache[idx] = constructed_model
                model_found = True

        if not model_found:
            constructed_model = _construct_model(model_type, model_value)
            queryset._result_cache.append(constructed_model)

    return queryset
