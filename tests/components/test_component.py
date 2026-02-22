import types

import orjson
import pytest
from tests.views.fake_components import (
    FakeAuthenticationComponent,
    FakeValidationComponent,
)

from django_unicorn.components import UnicornView
from django_unicorn.serializer import InvalidFieldNameError


class ExampleComponent(UnicornView):
    name = "World"

    def get_name(self):
        return "World"


@pytest.fixture()
def component():
    return ExampleComponent(component_id="asdf1234", component_name="example")


def test_init_with_template_name():
    class TestComponent(UnicornView):
        template_name = "unicorn/test.html"

    component = TestComponent(component_id="test_init_with_template_name", component_name="hello-world")
    assert component.template_name == "unicorn/test.html"


def test_init_with_get_template_names():
    class TestComponent(UnicornView):
        def get_template_names(self):
            return []

    component = TestComponent(component_id="test_init_with_get_template_names", component_name="hello-world")
    assert component.template_name is None


def test_init_attribute_names_cache(component):
    attribute_names_cache = component._attribute_names_cache
    assert len(attribute_names_cache) == 1
    assert attribute_names_cache[0] == "name"


def test_init_attribute_names(component):
    attribute_names = component._attribute_names()
    assert len(attribute_names) == 1
    assert attribute_names[0] == "name"


def test_init_attributes(component):
    attributes = component._attributes()
    assert len(attributes) == 1
    assert attributes["name"] == "World"


def test_init_properties():
    class TestComponent(UnicornView):
        @property
        def name(self):
            return "World"

    component = TestComponent(component_id="test_init_properties", component_name="hello-world")
    attributes = component._attributes()
    assert len(attributes) == 1
    assert attributes["name"] == "World"


def test_init_methods_cache(component):
    assert len(component._methods_cache) == 1


def test_init_methods(component):
    methods = component._methods()
    assert len(methods) == 1
    assert methods["get_name"]() == "World"


def test_get_frontend_context_variables_javascript_exclude(component):
    class Meta:
        javascript_exclude = ("name",)

    component.Meta = Meta

    frontend_context_variables = component.get_frontend_context_variables()
    frontend_context_variables_dict = orjson.loads(frontend_context_variables)
    assert len(frontend_context_variables_dict) == 0
    assert "name" not in frontend_context_variables_dict


def test_get_frontend_context_variables_javascript_exclude_invalid_field(component):
    class Meta:
        javascript_exclude = ("blob",)

    component.Meta = Meta

    with pytest.raises(InvalidFieldNameError):
        component.get_frontend_context_variables()


def test_get_frontend_context_variables_exclude_field(component):
    # Use internal class prevent class cache from causing issues
    class ExampleComponentWithMetaExclude(UnicornView):
        name = "world"

        class Meta:
            exclude = ("name",)

    component = ExampleComponentWithMetaExclude(
        component_id="test_get_frontend_context_variables_exclude_field", component_name="example"
    )

    frontend_context_variables = component.get_frontend_context_variables()
    frontend_context_variables_dict = orjson.loads(frontend_context_variables)
    assert len(frontend_context_variables_dict) == 0
    assert "name" not in frontend_context_variables_dict


def test_get_frontend_context_variables_exclude_field_invalid_type():
    # Use internal class prevent class cache from causing issues
    class ExampleComponentWithMetaInvalidExclude(UnicornView):
        name = "world"

        class Meta:
            exclude = ""

    with pytest.raises(AssertionError):
        ExampleComponentWithMetaInvalidExclude(
            component_id="test_get_frontend_context_variables_exclude_field_invalid_type", component_name="example"
        )


def test_get_frontend_context_variables_exclude_invalid_field():
    # Use internal class prevent class cache from causing issues
    class ExampleComponentWithMetaInvalidExclude(UnicornView):
        pass

        class Meta:
            exclude = ("blob",)

    with pytest.raises(InvalidFieldNameError):
        ExampleComponentWithMetaInvalidExclude(
            component_id="test_get_frontend_context_variables_exclude_invalid_field", component_name="example"
        )


def test_get_frontend_context_variables(component):
    frontend_context_variables = component.get_frontend_context_variables()
    frontend_context_variables_dict = orjson.loads(frontend_context_variables)
    assert len(frontend_context_variables_dict) == 1
    assert frontend_context_variables_dict.get("name") == "World"


def test_get_context_data(component):
    context_data = component.get_context_data()
    assert len(context_data) == 4  # `unicorn` and `view` are added to context data by default
    assert context_data.get("name") == "World"
    assert isinstance(context_data.get("get_name"), types.MethodType)


def test_get_context_data_component():
    class TestComponent(UnicornView):
        pass

    component = TestComponent(component_id="test_get_context_data_component", component_name="hello-world")
    actual = component.get_context_data()

    assert actual["unicorn"]
    assert actual["unicorn"]["component"] == component


def test_get_context_data_component_id():
    class TestComponent(UnicornView):
        pass

    component = TestComponent(component_id="test_get_context_data_component_id", component_name="hello-world")
    actual = component.get_context_data()

    assert actual["unicorn"]
    assert actual["unicorn"]["component_id"] == "test_get_context_data_component_id"


def test_get_context_data_component_name():
    class TestComponent(UnicornView):
        pass

    component = TestComponent(component_id="test_get_context_data_component_name", component_name="hello-world")
    actual = component.get_context_data()

    assert actual["unicorn"]
    assert actual["unicorn"]["component_name"] == "hello-world"


def test_get_context_data_component_key():
    class TestComponent(UnicornView):
        pass

    component = TestComponent(
        component_id="test_get_context_data_component_key",
        component_name="hello-world",
        component_key="key-key-key",
    )
    actual = component.get_context_data()

    assert actual["unicorn"]
    assert actual["unicorn"]["component_key"] == "key-key-key"


def test_call_queues_js_function(component):
    component.call("myFunction")
    assert component.calls == [{"fn": "myFunction", "args": ()}]


def test_call_queues_js_function_with_args(component):
    component.call("myFunction", "hello", 42)
    assert component.calls == [{"fn": "myFunction", "args": ("hello", 42)}]


def test_remove_queues_delete_component_call(component):
    component.remove()
    assert len(component.calls) == 1
    assert component.calls[0]["fn"] == "Unicorn.deleteComponent"
    assert component.calls[0]["args"] == (component.component_id,)


def test_remove_uses_own_component_id(component):
    component.remove()
    assert component.calls[0]["args"][0] == "asdf1234"


def test_remove_is_not_public_attribute(component):
    assert component._is_public("remove") is False


def test_is_public(component):
    assert component._is_public("test_name")


def test_is_public_protected(component):
    assert component._is_public("_test_name") is False


def test_is_public_http_method_names(component):
    assert component._is_public("http_method_names") is False


def test_meta_javascript_exclude():
    class TestComponent(UnicornView):
        name = "World"

        class Meta:
            javascript_exclude = ("name",)

    component = TestComponent(component_id="test_meta_javascript_exclude", component_name="hello-world")
    assert "name" not in component.get_frontend_context_variables()
    assert "name" in component.get_context_data()


def test_meta_javascript_exclude_nested_with_tuple():
    class TestComponent(UnicornView):
        name = {"Universe": {"World": "Earth"}}  # noqa: RUF012

        class Meta:
            javascript_exclude = ("name.Universe",)

    expected = '{"name":{}}'
    component = TestComponent(
        component_id="test_meta_javascript_exclude_nested_with_tuple", component_name="hello-world"
    )
    assert expected == component.get_frontend_context_variables()


def test_meta_javascript_exclude_nested_multiple_with_spaces():
    class TestComponent(UnicornView):
        name = {"Universe": {"World": "Earth"}}  # noqa: RUF012
        another = {"Neutral Milk Hotel": {"album": {"On Avery Island": 1996}}}  # noqa: RUF012

        class Meta:
            javascript_exclude = ("another.Neutral Milk Hotel.album",)

    expected = '{"another":{"Neutral Milk Hotel":{}},"name":{"Universe":{"World":"Earth"}}}'
    component = TestComponent(
        component_id="test_meta_javascript_exclude_nested_multiple_with_spaces", component_name="hello-world"
    )
    actual = component.get_frontend_context_variables()
    assert expected == actual


def test_meta_javascript_exclude_nested_with_list():
    class TestComponent(UnicornView):
        name = {"Universe": {"World": "Earth"}}  # noqa: RUF012

        class Meta:
            javascript_exclude = [  # noqa: RUF012
                "name.Universe",
            ]

    expected = '{"name":{}}'
    component = TestComponent(
        component_id="test_meta_javascript_exclude_nested_with_list", component_name="hello-world"
    )
    assert expected == component.get_frontend_context_variables()


def test_meta_exclude():
    class TestComponent(UnicornView):
        name = "World"

        class Meta:
            exclude = ("name",)

    component = TestComponent(component_id="test_meta_exclude", component_name="hello-world")
    assert "name" not in component.get_frontend_context_variables()
    assert "name" not in component.get_context_data()


def test_get_frontend_context_variables_form_with_boolean_field(component):
    """
    Form classes with BooleanField and CheckboxInput widget set the bool values to `None`
    without an explicit fix.
    """

    component = FakeValidationComponent(
        component_id="test_get_frontend_context_variables_form_with_boolean_field", component_name="example"
    )

    frontend_context_variables = component.get_frontend_context_variables()
    frontend_context_variables_dict = orjson.loads(frontend_context_variables)

    assert frontend_context_variables_dict.get("permanent") is not None


def test_get_frontend_context_variables_authentication_form(component):
    """
    `AuthenticationForm` have `request` as the first argument so `form_class` should
    init with data as a kwarg.
    """

    component = FakeAuthenticationComponent(
        component_id="test_get_frontend_context_variables_authentication_form", component_name="example"
    )

    component.get_frontend_context_variables()
