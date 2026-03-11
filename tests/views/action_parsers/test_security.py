import pytest

from django_unicorn.components import UnicornView
from django_unicorn.errors import UnicornViewError
from django_unicorn.views.action_parsers.call_method import _call_method_name
from django_unicorn.views.action_parsers.utils import set_property_value


class FakeSecurityComponent(UnicornView):
    template_name = "templates/test_component.html"
    name = "World"
    count = 0

    def save(self):
        return "saved"

    def increment(self):
        self.count += 1


# ── set_property_value: protected attributes should be rejected ─────────


def test_set_property_value_rejects_template_name():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_template_name")
    with pytest.raises(UnicornViewError, match="template_name"):
        set_property_value(component, "template_name", "/etc/passwd", data={})


def test_set_property_value_rejects_request():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_request")
    with pytest.raises(UnicornViewError, match="request"):
        set_property_value(component, "request", "hacked", data={})


def test_set_property_value_rejects_component_id():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_component_id")
    with pytest.raises(UnicornViewError, match="component_id"):
        set_property_value(component, "component_id", "hijacked", data={})


def test_set_property_value_rejects_component_name():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_component_name")
    with pytest.raises(UnicornViewError, match="component_name"):
        set_property_value(component, "component_name", "hijacked", data={})


def test_set_property_value_rejects_template_html():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_template_html")
    with pytest.raises(UnicornViewError, match="template_html"):
        set_property_value(component, "template_html", "<div>hacked</div>", data={})


def test_set_property_value_allows_public_property():
    """Public properties should still be settable."""
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_public_prop")
    data = {"name": "World"}
    set_property_value(component, "name", "Universe", data=data)
    assert component.name == "Universe"
    assert data["name"] == "Universe"


def test_set_property_value_rejects_underscore_prefix():
    """Properties starting with _ should be rejected."""
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_underscore")
    with pytest.raises(UnicornViewError):
        set_property_value(component, "_private_attr", "bad", data={})


# ── _call_method_name: protected methods should be rejected ─────────────


def test_call_method_name_rejects_reset():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_reset")
    with pytest.raises(UnicornViewError, match="reset"):
        _call_method_name(component, "reset", args=(), kwargs={})


def test_call_method_name_rejects_mount():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_mount")
    with pytest.raises(UnicornViewError, match="mount"):
        _call_method_name(component, "mount", args=(), kwargs={})


def test_call_method_name_rejects_render():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_render")
    with pytest.raises(UnicornViewError, match="render"):
        _call_method_name(component, "render", args=(), kwargs={})


def test_call_method_name_rejects_hydrate():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_hydrate")
    with pytest.raises(UnicornViewError, match="hydrate"):
        _call_method_name(component, "hydrate", args=(), kwargs={})


def test_call_method_name_rejects_dispatch():
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_dispatch")
    with pytest.raises(UnicornViewError, match="dispatch"):
        _call_method_name(component, "dispatch", args=(), kwargs={})


def test_call_method_name_allows_public_method():
    """Public methods should still be callable."""
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_public_method")
    result = _call_method_name(component, "save", args=(), kwargs={})
    assert result == "saved"


def test_call_method_name_allows_increment():
    """User-defined public methods should work normally."""
    component = FakeSecurityComponent(component_name="test", component_id="test_sec_increment")
    _call_method_name(component, "increment", args=(), kwargs={})
    assert component.count == 1


# ── Component.create: component name validation ────────────────────────


def test_component_create_rejects_path_traversal():
    """Component names with '..' should be rejected."""
    with pytest.raises(AssertionError, match="Invalid component name"):
        UnicornView.create(
            component_id="test_sec_traversal",
            component_name="../../etc/passwd",
        )


def test_component_create_rejects_double_dot():
    """Component names with '..' embedded should be rejected."""
    with pytest.raises(AssertionError, match="Invalid component name"):
        UnicornView.create(
            component_id="test_sec_traversal2",
            component_name="foo..bar",
        )
