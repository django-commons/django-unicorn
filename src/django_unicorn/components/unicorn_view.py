import importlib
import inspect
import logging
import pickle
import sys
from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any, Optional, cast

import shortuuid
from django.apps import apps as django_apps_module
from django.core.exceptions import NON_FIELD_ERRORS
from django.db.models import Model
from django.forms.widgets import CheckboxInput, Select
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.utils.decorators import classonlymethod
from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView

from django_unicorn import serializer
from django_unicorn.cacher import cache_full_tree, restore_from_cache
from django_unicorn.components.fields import UnicornField
from django_unicorn.components.unicorn_template_response import UnicornTemplateResponse
from django_unicorn.decorators import timed
from django_unicorn.errors import (
    ComponentClassLoadError,
    ComponentModuleLoadError,
    UnicornCacheError,
)
from django_unicorn.settings import get_setting
from django_unicorn.typer import cast_attribute_value, get_type_hints
from django_unicorn.utils import create_template, is_non_string_sequence

try:
    from cachetools.lru import LRUCache  # type: ignore
except ImportError:
    from cachetools import LRUCache


logger = logging.getLogger(__name__)


# TODO: Make maxsize configurable
location_cache = LRUCache(maxsize=100)

# Module cache to store the found component class by id
views_cache = LRUCache(maxsize=100)

# Module cache for constructed component classes
# This can create a subtle race condition so a more long-term solution needs to be found
constructed_views_cache = LRUCache(maxsize=100)
COMPONENTS_MODULE_CACHE_ENABLED = "pytest" not in sys.modules

STANDARD_COMPONENT_KWARG_KEYS = {
    "id",
    "component_id",
    "component_name",
    "component_key",
    "parent",
    "request",
}


def convert_to_snake_case(s: str) -> str:
    # TODO: Better handling of dash->snake
    return s.replace("-", "_")


def convert_to_dash_case(s: str) -> str:
    # TODO: Better handling of snake->dash
    return s.replace("_", "-")


def convert_to_pascal_case(s: str) -> str:
    # TODO: Better handling of dash/snake->pascal-case
    s = convert_to_snake_case(s)
    return "".join(word.title() for word in s.split("_"))


@lru_cache(maxsize=128, typed=True)
def get_locations(component_name: str) -> list[tuple[str, str]]:
    locations = []

    if "." in component_name:
        # Handle component names that specify a folder structure
        component_name = component_name.replace("/", ".")

        # Handle fully-qualified component names (e.g. `project.unicorn.HelloWorldView`)
        class_name = component_name.split(".")[-1:][0]
        module_name = component_name.replace(f".{class_name}", "")
        locations.append((module_name, class_name))

        # Assume if it ends with "View", then we don't need to add other
        if component_name.endswith("View") or component_name.endswith("Component"):
            return locations

    # Handle component names that specify a folder structure
    component_name = component_name.replace("/", ".")

    # Use conventions to find the component class
    class_name = convert_to_pascal_case(component_name)

    if "." in class_name:
        if class_name.split(".")[-1:]:
            class_name = class_name.split(".")[-1:][0]

    class_name = f"{class_name}View"
    module_name = convert_to_snake_case(component_name)

    # note - app_config.name gives the python path
    all_django_apps = [app_config.name for app_config in django_apps_module.get_app_configs()]
    unicorn_apps = get_setting("APPS", all_django_apps)

    if not is_non_string_sequence(unicorn_apps):
        raise AssertionError("APPS is expected to be a list, tuple or set")

    locations += [(f"{app}.components.{module_name}", class_name) for app in unicorn_apps]

    # Add default directory to the end of the list as a fallback
    locations.append((f"components.{module_name}", class_name))

    return locations


@timed
def construct_component(
    component_class,
    component_id,
    component_name,
    component_key,
    parent,
    request,
    component_args,
    **kwargs,
):
    """
    Constructs a class instance.
    """
    component = component_class(
        component_id=component_id,
        component_name=component_name,
        component_key=component_key,
        parent=parent,
        request=request,
        component_args=component_args,
        **kwargs,
    )

    component.calls = []
    

    component._mount_result = component.mount()
    component.hydrate()
    component.complete()
    component._validate_called = False

    return component


class Component(TemplateView):
    # These class variables are required to set these via kwargs
    component_name: str = ""
    component_key: str = ""
    component_id: str = ""
    component_args: list | None = None
    component_kwargs: dict | None = None

    def __init__(self, component_args: list | None = None, **kwargs):
        self.response_class = UnicornTemplateResponse

        self.component_name = kwargs.get("component_name", "")
        self.component_key: str = ""
        self.component_id: str = ""

        # Without these instance variables calling UnicornView() outside the
        # Django view/template logic (i.e. in unit tests) results in odd results.
        self.request: HttpRequest = HttpRequest()
        self.parent: Component | None = None
        self.children: list[Component] = []

        # Caches to reduce the amount of time introspecting the class
        self._methods_cache: dict[str, Callable] = {}
        self._attribute_names_cache: list[str] = []
        self._hook_methods_cache: list[str] = []

        # Dictionary with key: attribute name; value: pickled attribute value
        self._resettable_attributes_cache: dict[str, Any] = {}

        # JavaScript method calls
        self.calls: list[Any] = []

        # Default force render to False
        self.force_render = False

        super().__init__(**kwargs)

        if not self.component_name:
            raise AssertionError("Component name is required")

        if kwargs.get("id"):
            # Sometimes the component_id is initially in kwargs["id"]
            self.component_id = kwargs["id"]

        if not hasattr(self, "component_id"):
            raise AssertionError("Component id is required")

        if not self.component_id:
            raise AssertionError("Component id is required")

        self.component_cache_key = f"unicorn:component:{self.component_id}"

        if "request" in kwargs:
            self.setup(kwargs["request"])

        if "parent" in kwargs:
            self.parent = kwargs["parent"]

            if self.parent and self not in self.parent.children:
                self.parent.children.append(self)

        # Set component args
        self.component_args = component_args if component_args is not None else []

        # Only include custom kwargs since the standard kwargs are available
        # as instance variables
        custom_kwargs = set(kwargs.keys()) - STANDARD_COMPONENT_KWARG_KEYS
        self.component_kwargs = {k: kwargs[k] for k in list(custom_kwargs)}

        self._init_script: str = ""
        self._validate_called = False
        self.errors: dict[Any, Any] = {}
        self._set_default_template_name()
        self._set_caches()

    @timed
    def _set_default_template_name(self) -> None:
        """Sets a default template name based on component's name if necessary.

        Also handles `template_html` if it is set on the component which overrides `template_name`.
        """

        if hasattr(self, "template_html"):
            try:
                self.template_name = create_template(self.template_html)  # type: ignore
            except AssertionError:
                pass

        get_template_names_is_valid = False

        try:
            # Check for get_template_names by explicitly calling it since it
            # is a method on the parent class
            self.get_template_names()
            get_template_names_is_valid = True
            # pylint: disable=broad-except
        except Exception as e:
            logger.debug(e)

        if not self.template_name and not get_template_names_is_valid:
            # Convert component name with a dot to a folder structure
            template_name = self.component_name.replace(".", "/")
            self.template_name = f"unicorn/{template_name}.html"

    def _handle_validation_error(self, e):
        # validation error handling
        min_validation_error_args = 2

        if len(e.args) < min_validation_error_args or not e.args[1]:
            raise AssertionError("Error code must be specified") from e

        if hasattr(e, "error_list"):
            error_code = e.args[1]
            for error in e.error_list:
                if NON_FIELD_ERRORS in self.errors:
                    self.errors[NON_FIELD_ERRORS].append({"code": error_code, "message": error.message})
                else:
                    self.errors[NON_FIELD_ERRORS] = [{"code": error_code, "message": error.message}]
        elif hasattr(e, "message_dict"):
            for field, message in e.message_dict.items():
                if not e.args[1]:
                    raise AssertionError("Error code must be specified") from e
                error_code = e.args[1]
                if field in self.errors:
                    self.errors[field].append({"code": error_code, "message": message})
                else:
                    self.errors[field] = [{"code": error_code, "message": message}]

    def _handle_safe_fields(self):
        safe_fields = []
        if hasattr(self, "Meta") and hasattr(self.Meta, "safe"):
            if isinstance(self.Meta.safe, list | tuple):
                for field_name in self.Meta.safe:
                    if field_name in self._attributes().keys():
                        safe_fields.append(field_name)

        for field_name in safe_fields:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, mark_safe(value))  # noqa: S308

    @timed
    def _set_caches(self) -> None:
        """
        Setup some initial "caches" to prevent Python from having to introspect
        a component UnicornView for methods and properties multiple times.
        """
        self._attribute_names_cache = self._attribute_names()
        self._set_hook_methods_cache()
        self._methods_cache = self._methods()
        self._set_resettable_attributes_cache()

    @timed
    def reset(self):
        for (
            attribute_name,
            pickled_value,
        ) in self._resettable_attributes_cache.items():
            try:
                attribute_value = pickle.loads(pickled_value)  # noqa: S301
                self._set_property(attribute_name, attribute_value)
            except TypeError:
                logger.warning(f"Resetting '{attribute_name}' attribute failed because it could not be constructed.")
                pass
            except pickle.PickleError:
                logger.warning(f"Resetting '{attribute_name}' attribute failed because it could not be de-pickled.")
                pass

    def call(self, function_name, *args):
        """
        Add a JavaScript method name and arguments to be called after the component is rendered.
        """
        self.calls.append({"fn": function_name, "args": args})

    def remove(self):
        """
        Remove this component's root element from the DOM and delete it from the
        internal component store. Equivalent to calling
        ``self.call("Unicorn.deleteComponent", self.component_id)``.
        """
        self.call("Unicorn.deleteComponent", self.component_id)

    def mount(self):
        """
        Hook that gets called when the component is first created.
        """
        pass

    def hydrate(self):
        """
        Hook that gets called when the component's data is hydrated.
        """
        pass

    def complete(self):
        """
        Hook that gets called after all component methods are executed.
        """
        pass

    def rendered(self, html):
        """
        Hook that gets called after the component has been rendered.
        """
        pass

    def parent_rendered(self, html):
        """
        Hook that gets called after the component's parent has been rendered.
        """
        pass

    def updating(self, name, value):
        """
        Hook that gets called when a component's data is about to get updated.
        """
        pass

    def updated(self, name, value):
        """
        Hook that gets called when a component's data is updated.
        """
        pass

    def resolved(self, name, value):
        """
        Hook that gets called when a component's data is resolved.
        """
        pass

    def calling(self, name, args):
        """
        Hook that gets called when a component's method is about to get called.
        """
        pass

    def called(self, name, args):
        """
        Hook that gets called when a component's method is called.
        """
        pass

    def pre_parse(self):
        """
        Hook that gets called before the data is parsed and applied to the component.
        """
        pass

    def post_parse(self):
        """
        Hook that gets called after the data is parsed and applied to the component.
        """
        pass

    @timed
    def render(self, *, init_js=False, extra_context=None, request=None) -> str:
        """
        Renders a UnicornView component with the public properties available. Delegates to a
        UnicornTemplateResponse to actually render a response.

        Args:
            param init_js: Whether or not to include the Javascript required to initialize the component.
            param extra_context:
            param request: Set the `request` for rendering. Usually it will be in the context,
                but it is missing when the component is re-rendered as a direct view, so it needs
                to be set explicitly.
        """

        if extra_context is not None:
            self.extra_context = extra_context

        if request:
            self.request = request

        if hasattr(self, "_mount_result") and self._mount_result:
            if isinstance(self._mount_result, HttpResponseRedirect):
                return f"<script>window.location.href = '{self._mount_result.url}';</script>"

        response = self.render_to_response(
            context=self.get_context_data(),
            component=self,
            init_js=init_js,
        )

        # render_to_response() could only return a HttpResponse, so check for render()
        if hasattr(response, "render"):
            cast(Any, response).render()

        rendered_component = response.content.decode("utf-8")

        return rendered_component

    def dispatch(self, request, *args, **kwargs):  # noqa: ARG002
        """
        Called by the `as_view` class method when utilizing a component directly as a view.
        """

        self._mount_result = self.mount()
        if self._mount_result and isinstance(self._mount_result, HttpResponse):
            return self._mount_result

        self.hydrate()

        return self.render_to_response(
            context=self.get_context_data(),
            component=self,
            init_js=True,
        )

    def _cache_component(self, *, parent=None, component_args=None, **kwargs):
        """
        Cache the component in the module and the Django cache.
        """

        # Put the location for the component name in a module cache
        location_cache[self.component_name] = (self.__module__, self.__class__.__name__)

        # Put the component's class in a module cache
        views_cache[self.component_id] = (
            self.__class__,
            parent,
            component_args,
            kwargs,
        )

        # Put the instantiated component into a module cache and the Django cache
        try:
            if COMPONENTS_MODULE_CACHE_ENABLED:
                constructed_views_cache[self.component_id] = self

            cache_full_tree(self)
        except UnicornCacheError as e:
            logger.warning(e)

    @timed
    def get_frontend_context_variables(self) -> str:
        """
        Get publicly available properties and output them in a string-encoded JSON object.
        """

        frontend_context_variables = {}
        attributes = self._attributes()
        frontend_context_variables.update(attributes)

        exclude_field_attributes: list[str] = []

        # Remove any field in `javascript_exclude` from `frontend_context_variables`
        if hasattr(self, "Meta") and hasattr(self.Meta, "javascript_exclude"):
            if isinstance(self.Meta.javascript_exclude, Sequence):
                for field_name in self.Meta.javascript_exclude:
                    if "." in cast(str, field_name):
                        # Because the dictionary value could be an object, we can't just remove the attribute, so
                        # store field attributes for later to remove them from the serialized dictionary
                        exclude_field_attributes.append(cast(str, field_name))
                    else:
                        if field_name not in frontend_context_variables:
                            raise serializer.InvalidFieldNameError(
                                field_name=cast(str, field_name), data=cast(dict, frontend_context_variables)
                            )

                        del frontend_context_variables[field_name]

        # Add cleaned values to `frontend_content_variables` based on the widget in form's fields
        form = self._get_form(attributes)

        if form:
            for key in attributes.keys():
                if key in form.fields:
                    field = form.fields[key]

                    if key in form.cleaned_data:
                        cleaned_value = form.cleaned_data[key]

                        if isinstance(field.widget, CheckboxInput) and isinstance(cleaned_value, bool):
                            # Handle booleans for checkboxes explicitly because `format_value`
                            # returns `None`
                            value = cleaned_value
                        elif isinstance(field.widget, Select) and not field.widget.allow_multiple_selected:
                            # Handle value for Select widgets explicitly because `format_value`
                            # returns a list of stringified values
                            value = cleaned_value
                        else:
                            value = field.widget.format_value(cleaned_value)

                        # Don't update the frontend variable if the only change is
                        # stripping off the whitespace from the field value
                        # https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.CharField.strip
                        if (
                            not hasattr(frontend_context_variables[key], "strip")
                            or frontend_context_variables[key].strip() != value
                        ):
                            frontend_context_variables[key] = value

        encoded_frontend_context_variables = serializer.dumps(
            frontend_context_variables,
            exclude_field_attributes=tuple(exclude_field_attributes),
        )

        return encoded_frontend_context_variables

    @timed
    def _get_form(self, data):
        if hasattr(self, "form_class"):
            try:
                form = cast(Callable, self.form_class)(data=data)
                form.is_valid()

                return form
            except Exception as e:
                logger.exception(e)

    @timed
    def get_context_data(self, **kwargs):
        """
        Overrides the standard `get_context_data` to add in publicly available
        properties and methods.
        """

        context = super().get_context_data(**kwargs)

        attributes = self._attributes()
        context.update(attributes)
        context.update(self._methods())
        context.update(
            {
                "unicorn": {
                    "component_id": self.component_id,
                    "component_name": self.component_name,
                    "component_key": self.component_key,
                    "component": self,
                    "errors": self.errors,
                }
            }
        )

        return context

    @timed
    def is_valid(self, model_names: list | None = None) -> bool:
        return len(self.validate(model_names).keys()) == 0

    @timed
    def validate(self, model_names: list | None = None) -> dict:
        """
        Validates the data using the `form_class` set on the component.

        Args:
            model_names: Only include validation errors for specified fields. If none, validate everything.
        """
        # TODO: Handle form.non_field_errors()?

        if self._validate_called:
            return self.errors

        self._validate_called = True

        data = self._attributes()
        form = self._get_form(data)

        if form:
            form_errors = form.errors.get_json_data(escape_html=True)

            # This code is confusing, but handles this use-case:
            # the component has two models, one that starts with an error and one
            # that is valid. Validating the valid one should not show an error for
            # the invalid one. Only after the invalid field is updated, should the
            # error show up and persist, even after updating the valid form.
            if self.errors:
                keys_to_remove = []

                for key, value in self.errors.items():
                    if key in form_errors:
                        self.errors[key] = value
                    else:
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    self.errors.pop(key)

            if model_names is not None:
                for key, value in form_errors.items():
                    if key in model_names:
                        self.errors[key] = value
            else:
                self.errors.update(form_errors)

        return self.errors

    @timed
    def _attribute_names(self) -> list[str]:
        """
        Gets publicly available attribute names. Cached in `_attribute_names_cache`.
        """
        non_callables = [member[0] for member in inspect.getmembers(self, lambda x: not callable(x))]
        attribute_names = [name for name in non_callables if self._is_public(name)]

        # Add type hints for the component to the attribute names since
        # they won't be returned from `getmembers`
        for type_hint_attribute_name in get_type_hints(self).keys():
            if self._is_public(type_hint_attribute_name):
                if type_hint_attribute_name not in attribute_names:
                    attribute_names.append(type_hint_attribute_name)

        return attribute_names

    @timed
    def _attributes(self) -> dict[str, Any]:
        """
        Get publicly available attributes and their values from the component.
        """

        attribute_names = self._attribute_names_cache
        attributes = {}

        for attribute_name in attribute_names:
            attributes[attribute_name] = getattr(self, attribute_name, None)

        return attributes

    @timed
    def _set_property(
        self,
        name: str,
        value: Any,
        *,
        call_updating_method: bool = False,
        call_updated_method: bool = False,
        call_resolved_method: bool = False,
    ) -> None:
        # Get the correct value type by using the form if it is available
        data = self._attributes()

        value = cast_attribute_value(self, name, value)
        data[name] = value

        form = self._get_form(data)

        if form and name in form.fields and name in form.cleaned_data:
            # The Django form CharField validator will remove whitespace
            # from the field value. Ignore that update if it's the
            # only thing different from the validator
            # https://docs.djangoproject.com/en/stable/ref/forms/fields/#django.forms.CharField.strip
            if not hasattr(value, "strip") or form.cleaned_data[name] != value.strip():
                value = form.cleaned_data[name]

        if call_updating_method:
            updating_function_name = f"updating_{name}"

            if hasattr(self, updating_function_name):
                getattr(self, updating_function_name)(value)

        try:
            setattr(self, name, value)

            if call_updated_method:
                updated_function_name = f"updated_{name}"

                if hasattr(self, updated_function_name):
                    getattr(self, updated_function_name)(value)

            if call_resolved_method:
                resolved_function_name = f"resolved_{name}"

                if hasattr(self, resolved_function_name):
                    getattr(self, resolved_function_name)(value)
        except AttributeError:
            raise

    @timed
    def _methods(self) -> dict[str, Callable]:
        """
        Get publicly available method names and their functions from the component.
        Cached in `_methods_cache`.
        """

        if self._methods_cache:
            return self._methods_cache

        member_methods = inspect.getmembers(self, inspect.ismethod)
        public_methods = [method for method in member_methods if self._is_public(method[0])]
        methods = dict(public_methods)
        self._methods_cache = methods

        return methods

    @timed
    def _set_hook_methods_cache(self) -> None:
        """
        Caches the updating/updated attribute function names defined on the component.
        """
        self._hook_methods_cache = []

        for attribute_name in self._attribute_names_cache:
            updating_function_name = f"updating_{attribute_name}"
            updated_function_name = f"updated_{attribute_name}"
            hook_function_names = [updating_function_name, updated_function_name]

            for function_name in hook_function_names:
                if hasattr(self, function_name):
                    self._hook_methods_cache.append(function_name)

    @timed
    def _set_resettable_attributes_cache(self) -> None:
        """
        Caches the attributes that are "resettable" in `_resettable_attributes_cache`.
        Cache is a dictionary with key: attribute name; value: pickled attribute value

        Examples:
            - `UnicornField`
            - Django Models without a defined pk
        """
        self._resettable_attributes_cache = {}

        for attribute_name, attribute_value in self._attributes().items():
            if isinstance(attribute_value, UnicornField):
                self._resettable_attributes_cache[attribute_name] = pickle.dumps(attribute_value)
            elif isinstance(attribute_value, Model):
                if not attribute_value.pk:
                    if attribute_name not in self._resettable_attributes_cache:
                        try:
                            self._resettable_attributes_cache[attribute_name] = pickle.dumps(attribute_value)
                        except pickle.PickleError:
                            logger.warning(f"Caching '{attribute_name}' failed because it could not be pickled.")
                            pass

    def _is_public(self, name: str) -> bool:
        """
        Determines if the name should be sent in the context.
        """

        # Ignore some standard attributes from TemplateView
        protected_names = (
            "render",
            "request",
            "args",
            "kwargs",
            "content_type",
            "extra_context",
            "http_method_names",
            "template_engine",
            "template_name",
            "template_html",
            "dispatch",
            "id",
            "get",
            "get_context_data",
            "get_template_names",
            "render_to_response",
            "http_method_not_allowed",
            "options",
            "setup",
            "fill",
            "view_is_async",
            # Component methods
            "component_id",
            "component_name",
            "component_key",
            "reset",
            "mount",
            "hydrate",
            "updating",
            "update",
            "calling",
            "called",
            "complete",
            "rendered",
            "parent_rendered",
            "validate",
            "is_valid",
            "get_frontend_context_variables",
            "errors",
            "updated",
            "resolved",
            "parent",
            "children",
            "call",
            "remove",
            "calls",
            "component_cache_key",
            "component_kwargs",
            "component_args",
            "force_render",
            # Lifecycle hooks
            "pre_parse",
            "post_parse",
            "hydrate",
            "complete",
            "rendered",
            "parent_rendered",
            "updating",
            "updated",
            "resolved",
            "calling",
            "called",
        )
        excludes = []

        if hasattr(self, "Meta") and hasattr(self.Meta, "exclude"):
            if not is_non_string_sequence(self.Meta.exclude):
                raise AssertionError("Meta.exclude should be a list, tuple, or set")

            meta_exclude = cast(Sequence[str], self.Meta.exclude)

            for exclude in meta_exclude:
                if not hasattr(self, str(exclude)):
                    raise serializer.InvalidFieldNameError(field_name=str(exclude), data=self._attributes())

            excludes = meta_exclude

        return not (
            name.startswith("_") or name in protected_names or name in self._hook_methods_cache or name in excludes
        )

    @staticmethod
    @timed
    def create(
        *,
        component_id: str,
        component_name: str,
        component_key: str = "",
        parent: Optional["Component"] = None,
        request: HttpRequest | None = None,
        use_cache=True,
        component_args: list | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> "Component":
        """
        Find and instantiate a component class based on `component_name`.

        Args:
            param component_id: Id of the component. Required.
            param component_name: Name of the component. Used to locate the correct `UnicornView`
                component class and template if necessary. Required.
            param component_key: Key of the component to allow multiple components of the same name
                to be differentiated. Optional.
            param parent: The parent component of the current component.
            param component_args: Arguments for the component passed in from the template. Defaults to `[]`.
            param kwargs: Keyword arguments for the component passed in from the template. Defaults to `{}`.

        Returns:
            Instantiated `UnicornView` component.
            Raises `ComponentModuleLoadError` or `ComponentClassLoadError` if the component could not be loaded.
        """
        if not component_id:
            raise AssertionError("Component id is required")
        if not component_name:
            raise AssertionError("Component name is required")

        component_args = component_args if component_args is not None else []
        kwargs = kwargs if kwargs is not None else {}

        @timed
        def _get_component_class(module_name: str, class_name: str) -> type[Component]:
            """
            Imports a component based on module and class name.
            """
            module = importlib.import_module(module_name)
            component_class = getattr(module, class_name)

            return component_class

        component_cache_key = f"unicorn:component:{component_id}"
        cached_component = restore_from_cache(component_cache_key, request=request)

        if not cached_component:
            # Note that `hydrate()` and `complete` don't need to be called here
            # because this path only happens for re-rendering from the view
            cached_component = constructed_views_cache.get(component_id)

            if cached_component:
                cached_component.setup(request)
                cached_component._validate_called = False
                cached_component.calls = []

        if use_cache and cached_component:
            logger.debug(f"Retrieve {component_id} from constructed views cache")

            cached_component.component_args = component_args
            cached_component.component_kwargs = kwargs

            # TODO: How should args be handled?
            # Set kwargs onto the cached component
            for key, value in kwargs.items():
                if hasattr(cached_component, key):
                    setattr(cached_component, key, value)

            cached_component._cache_component(parent=parent, component_args=component_args, **kwargs)

            # Call hydrate because the component will be re-rendered
            cached_component.hydrate()

            return cached_component

        if component_id in views_cache:
            (component_class, parent, component_args, kwargs) = views_cache[component_id]

            component = construct_component(
                component_class=component_class,
                component_id=component_id,
                component_name=component_name,
                component_key=component_key,
                parent=parent,
                request=request,
                component_args=component_args,
                **kwargs,
            )  # type: ignore
            logger.debug(f"Retrieve {component_id} from views cache")

            return component

        # Check for explicitly defined component
        components_setting = get_setting("COMPONENTS", {})
        component_class_from_setting = components_setting.get(component_name)

        if component_class_from_setting:
            component_from_setting = construct_component(
                component_class=component_class_from_setting,
                component_id=component_id,
                component_name=component_name,
                component_key=component_key,
                parent=parent,
                request=request,
                component_args=component_args,
                **kwargs,
            )

            component_from_setting._cache_component(parent=parent, component_args=component_args, **kwargs)

            return component_from_setting

        locations = []

        if component_name in location_cache:
            locations.append(location_cache[component_name])
        else:
            locations = get_locations(component_name)

        class_name_not_found = None
        attribute_exception = None

        for module_name, class_name in locations:
            try:
                component_class = _get_component_class(module_name, class_name)

                component = construct_component(
                    component_class=component_class,
                    component_id=component_id,
                    component_name=component_name,
                    component_key=component_key,
                    parent=parent,
                    request=request,
                    component_args=component_args,
                    **kwargs,
                )

                component._cache_component(parent=parent, component_args=component_args, **kwargs)

                return component
            except ModuleNotFoundError as e:
                logger.debug(e)
                pass
            except AttributeError as e:
                logger.debug(e)
                attribute_exception = e
                class_name_not_found = f"{module_name}.{class_name}"

        if class_name_not_found is not None and attribute_exception is not None:
            message = f"The component class '{class_name_not_found}' could not be loaded: {attribute_exception}"
            raise ComponentClassLoadError(message, locations=locations) from attribute_exception

        module_name_not_found = component_name.replace("-", "_")
        message = f"The component module '{module_name_not_found}' could not be loaded."

        raise ComponentModuleLoadError(message, locations=locations)

    @classonlymethod
    def as_view(cls, **initkwargs):  # noqa: N805
        if "component_id" not in initkwargs:
            initkwargs["component_id"] = shortuuid.uuid()[:8]

        if "component_name" not in initkwargs:
            module_name = cls.__module__
            module_parts = module_name.split(".")
            component_name = module_parts[len(module_parts) - 1]
            component_name = convert_to_dash_case(component_name)

            initkwargs["component_name"] = component_name

        return super().as_view(**initkwargs)


UnicornView = Component
