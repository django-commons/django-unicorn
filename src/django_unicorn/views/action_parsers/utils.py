from typing import Any

from django.db.models import QuerySet

from django_unicorn.components import UnicornView
from django_unicorn.decorators import timed
from django_unicorn.signals import (
    component_property_resolved,
    component_property_updated,
    component_property_updating,
)


@timed
def set_property_value(
    component: UnicornView,
    property_name: str | None,
    property_value: Any,
    data: dict | None = None,
    call_resolved_method=True,  # noqa: FBT002
) -> None:
    """
    Sets properties on the component.
    Also updates the data dictionary which gets set back as part of the payload.

    Args:
        param component: Component to set attributes on.
        param property_name: Name of the property.
        param property_value: Value to set on the property.
        param data: Dictionary that gets sent back with the response. Defaults to {}.
        call_resolved_method: Whether or not to call the resolved method. Defaults to True.
    """

    if property_name is None:
        raise AssertionError("Property name is required")
    if property_value is None:
        raise AssertionError("Property value is required")

    if not data:
        data = {}

    component.updating(property_name, property_value)
    component_property_updating.send(
        sender=component.__class__, component=component, name=property_name, value=property_value
    )

    """
    Handles nested properties. For example, for the following component:

    class Author(UnicornField):
        name = "Neil"

    class TestView(UnicornView):
        author = Author()

    `payload` would be `{'name': 'author.name', 'value': 'Neil Gaiman'}`

    The following code updates UnicornView.author.name based the payload's `author.name`.
    """
    property_name_parts = property_name.split(".")
    for part in property_name_parts:
        if part.startswith("__") and part.endswith("__"):
            raise AssertionError("Invalid property name")
    component_or_field: Any = component
    data_or_dict = data  # Could be an internal portion of data that gets set

    for idx, property_name_part in enumerate(property_name_parts):
        if hasattr(component_or_field, property_name_part):
            if idx == len(property_name_parts) - 1:
                if hasattr(component_or_field, "_set_property"):
                    # Can assume that `component_or_field` is a component
                    component_or_field._set_property(
                        property_name_part,
                        property_value,
                        call_updating_method=False,  # the updating method has already been called above
                        call_updated_method=True,
                        call_resolved_method=call_resolved_method,
                    )
                else:
                    # Handle calling the updating/updated method for nested properties
                    property_name_snake_case = property_name.replace(".", "_")
                    updating_function_name = f"updating_{property_name_snake_case}"
                    updated_function_name = f"updated_{property_name_snake_case}"
                    resolved_function_name = f"resolved_{property_name_snake_case}"

                    if hasattr(component, updating_function_name):
                        getattr(component, updating_function_name)(property_value)

                    is_relation_field = False

                    # Set the id property for ForeignKeys
                    # TODO: Move some of this to utility function
                    if hasattr(component_or_field, "_meta"):
                        for field in component_or_field._meta.get_fields():
                            if field.is_relation and field.many_to_many:
                                related_name = field.name

                                if field.auto_created:
                                    related_name = field.related_name or f"{field.name}_set"

                                if related_name == property_name_part:
                                    related_descriptor = getattr(component_or_field, related_name)
                                    related_descriptor.set(property_value)
                                    is_relation_field = True
                                    break
                            elif field.name == property_name_part:
                                if field.is_relation:
                                    setattr(
                                        component_or_field,
                                        field.attname,
                                        property_value,
                                    )
                                    is_relation_field = True
                                    break

                    if not is_relation_field:
                        setattr(component_or_field, property_name_part, property_value)

                    if hasattr(component, updated_function_name):
                        getattr(component, updated_function_name)(property_value)

                    if call_resolved_method and hasattr(component, resolved_function_name):
                        getattr(component, resolved_function_name)(property_value)

                data_or_dict[property_name_part] = property_value
            else:
                component_or_field = getattr(component_or_field, property_name_part)
                data_or_dict = data_or_dict.get(property_name_part, {})
        elif isinstance(component_or_field, dict):
            if idx == len(property_name_parts) - 1:
                component_or_field[property_name_part] = property_value  # type: ignore[index]
                data_or_dict[property_name_part] = property_value
            else:
                component_or_field = component_or_field[property_name_part]
                data_or_dict = data_or_dict.get(property_name_part, {})
        elif isinstance(component_or_field, QuerySet | list):
            # TODO: Check for iterable instead of list? `from collections.abc import Iterable`
            property_name_part_int = int(property_name_part)

            if idx == len(property_name_parts) - 1:
                component_or_field[property_name_part_int] = property_value  # type: ignore[index]
                data_or_dict[property_name_part_int] = property_value
            else:
                component_or_field = component_or_field[property_name_part_int]  # type: ignore[index]
                data_or_dict = data_or_dict[property_name_part_int]
        else:
            break

    component.updated(property_name, property_value)
    component_property_updated.send(
        sender=component.__class__, component=component, name=property_name, value=property_value
    )

    if call_resolved_method:
        component.resolved(property_name, property_value)
        component_property_resolved.send(
            sender=component.__class__, component=component, name=property_name, value=property_value
        )
