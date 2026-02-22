import logging
from dataclasses import is_dataclass
from typing import Any, Union, cast, get_args, get_origin

from django.db.models import Field, Model

from django_unicorn.components import UnicornField, UnicornView
from django_unicorn.decorators import timed
from django_unicorn.typer import (
    cast_value,
    create_queryset,
    get_type_hints,
    is_queryset,
)

try:
    from types import UnionType
except ImportError:
    UnionType = Union  # type: ignore


logger = logging.getLogger(__name__)


@timed
def set_property_from_data(
    component_or_field: UnicornView | UnicornField | Model,
    name: str,
    value: Any,
    *,
    ignore_m2m: bool = False,
) -> None:
    """
    Sets properties on the component based on passed-in data.
    """

    try:
        if not hasattr(component_or_field, name):
            return
    except ValueError:
        # Treat ValueError the same as a missing field because trying to access a many-to-many
        # field before the model's pk will throw this exception
        return

    field = getattr(component_or_field, name)
    component_field_is_model_or_unicorn_field = _is_component_field_model_or_unicorn_field(component_or_field, name)

    if isinstance(component_or_field, Model) and not isinstance(value, dict):
        # If the component is a model, we might need to set a foreign key by its ID
        try:
            model_field = component_or_field._meta.get_field(name)

            if model_field.is_relation and model_field.many_to_one:
                if isinstance(value, Model):
                    setattr(component_or_field, name, value)
                elif isinstance(model_field, Field):
                    setattr(component_or_field, model_field.attname, value)
                return
        except Exception as exc:
            logger.exception(exc)

    # UnicornField and Models are always a dictionary (can be nested)
    if component_field_is_model_or_unicorn_field:
        # Re-get the field since it might have been set in `_is_component_field_model_or_unicorn_field`
        field = getattr(component_or_field, name)

        type_hints = get_type_hints(component_or_field)

        if isinstance(value, dict):
            for key in value.keys():
                key_value = value[key]
                set_property_from_data(field, key, key_value, ignore_m2m=ignore_m2m)
    elif hasattr(field, "related_val"):
        # Use `related_val` to check for many-to-many
        if not ignore_m2m:
            field.set(value)
    else:
        # TODO: Call django_unicorn.typing.cast_attribute_value?
        type_hints = get_type_hints(component_or_field)
        type_hint = type_hints.get(name)

        if is_queryset(field, type_hint, value):
            value = create_queryset(field, type_hint, value)
        elif type_hint:
            if is_dataclass(type_hint):
                value = type_hint(**value)
            else:
                try:
                    value = cast_value(type_hint, value)
                except TypeError:
                    # Ignore this exception because some type-hints can't be instantiated like this (e.g. `List[]`)
                    pass

        if hasattr(component_or_field, "_set_property"):
            # Can assume that `component_or_field` is a component
            cast(UnicornView, component_or_field)._set_property(
                name, value, call_updating_method=True, call_updated_method=False
            )
        else:
            setattr(component_or_field, name, value)


@timed
def _is_component_field_model_or_unicorn_field(
    component_or_field: UnicornView | UnicornField | Model,
    name: str,
) -> bool:
    """
    Determines whether a component's field is a Django `Model` or `UnicornField` either
    by checking the field's instance or inspecting the type hints.

    One side-effect is that the field will be instantiated if it is currently `None` and
    the type hint is available.

    Args:
        component: `UnicornView` to check.
        name: Name of the field.

    Returns:
        Whether the field is a Django `Model` or `UnicornField`.
    """
    field = getattr(component_or_field, name)

    if isinstance(field, Model | UnicornField):
        return True

    is_subclass_of_model = False
    is_subclass_of_unicorn_field = False
    component_type_hints = {}

    try:
        component_type_hints = get_type_hints(component_or_field)

        if name in component_type_hints:
            type_hint = component_type_hints[name]

            if get_origin(type_hint) is Union or get_origin(type_hint) is UnionType:
                for arg in get_args(type_hint):
                    if arg is not type(None):
                        type_hint = arg
                        break

            is_subclass_of_model = issubclass(type_hint, Model)

            if not is_subclass_of_model:
                is_subclass_of_unicorn_field = issubclass(type_hint, UnicornField)

            # Construct a new class if the field is None and there is a type hint available
            if field is None:
                if is_subclass_of_model or is_subclass_of_unicorn_field:
                    field = type_hint()
                    setattr(component_or_field, name, field)
    except TypeError:
        pass

    return is_subclass_of_model or is_subclass_of_unicorn_field
