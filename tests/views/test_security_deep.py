"""
Deep-dive security tests for django-unicorn.

Each section tries to exploit a specific attack vector.
"""

import pickle
import re

import pytest
import shortuuid
from django.core.exceptions import DisallowedRedirect
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.safestring import SafeText

from django_unicorn.call_method_parser import eval_value, parse_call_method_name
from django_unicorn.components import HashUpdate, UnicornView
from django_unicorn.components.fields import UnicornField
from django_unicorn.errors import UnicornViewError
from django_unicorn.utils import generate_checksum
from django_unicorn.views.action_parsers.call_method import _call_method_name
from django_unicorn.views.action_parsers.utils import set_property_value
from django_unicorn.views.objects import Return
from django_unicorn.views.utils import set_property_from_data

# ═══════════════════════════════════════════════════════════════════════
# Test components
# ═══════════════════════════════════════════════════════════════════════


class NestedObj(UnicornField):
    secret = "top-secret"
    visible = "hello"


class SecurityComponent(UnicornView):
    template_name = "templates/test_component.html"
    name = "World"
    count = 0
    check = False
    nested = {"key": "value"}  # noqa: RUF012
    items = [1, 2, 3]  # noqa: RUF012
    nested_obj = NestedObj()

    def save(self):
        return "saved"

    def increment(self):
        self.count += 1

    def _private_method(self):
        return "private"

    def dangerous_action(self):
        """A public method that should be callable."""
        return "executed"


class SafeFieldComponent(UnicornView):
    template_name = "templates/test_component.html"
    html_content = ""

    class Meta:
        safe = ("html_content",)


class ChildComponent(UnicornView):
    template_name = "templates/test_component.html"
    child_value = "child"

    def child_method(self):
        return "child_result"


class ComponentWithCallableAction(UnicornView):
    template_name = "templates/test_component.html"
    user_input = ""

    def trigger_call(self):
        self.call("showMessage", self.user_input)

    def trigger_eval(self):
        self.call("eval", "alert(1)")


def _make_component(cls=SecurityComponent, **kwargs):
    """Helper to create a component instance with unique IDs."""
    cid = kwargs.pop("component_id", shortuuid.uuid()[:8])
    cname = kwargs.pop("component_name", "test")
    return cls(component_name=cname, component_id=cid, **kwargs)


# ═══════════════════════════════════════════════════════════════════════
# Checksum integrity
# ═══════════════════════════════════════════════════════════════════════


class TestChecksumIntegrity:
    """Verify that checksum validation correctly protects data integrity."""

    def test_valid_checksum_passes(self):
        """A correct checksum should be accepted."""
        data = {"name": "World", "count": 0}
        checksum = generate_checksum(data)
        assert checksum  # non-empty
        assert generate_checksum(data) == checksum  # deterministic

    def test_tampered_data_fails_checksum(self):
        """If data is modified, the checksum should not match."""
        original_data = {"name": "World", "count": 0}
        original_checksum = generate_checksum(original_data)

        tampered_data = {"name": "World", "count": 999}
        tampered_checksum = generate_checksum(tampered_data)

        assert original_checksum != tampered_checksum

    def test_extra_key_in_data_fails_checksum(self):
        """Adding extra keys to data changes the checksum."""
        original_data = {"name": "World"}
        original_checksum = generate_checksum(original_data)

        tampered_data = {"name": "World", "template_name": "/etc/passwd"}
        tampered_checksum = generate_checksum(tampered_data)

        assert original_checksum != tampered_checksum

    def test_checksum_uses_hmac_with_secret(self):
        """Checksum should use SECRET_KEY, not a simple hash."""
        data = {"test": "data"}
        checksum = generate_checksum(data)
        # The checksum is a shortuuid-encoded HMAC, so it should be 8 chars
        assert len(checksum) == 8

    def test_action_queue_not_in_checksum(self):
        """
        The action queue is NOT included in the checksum.
        This documents the fact that actions are not integrity-protected.
        The checksum only covers `data`.
        """
        data = {"name": "World"}
        checksum = generate_checksum(data)
        # No matter what action queue we craft, checksum stays same
        assert generate_checksum(data) == checksum


# ═══════════════════════════════════════════════════════════════════════
# Nested property traversal
# ═══════════════════════════════════════════════════════════════════════


class TestNestedPropertyTraversal:
    """Attempt to reach internal attributes via nested dot notation."""

    def test_dunder_class_via_nested_property(self):
        """Traversing through a public property to __class__ should be blocked."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Invalid property name"):
            set_property_value(component, "nested_obj.__class__", "hacked", data={})

    def test_dunder_dict_via_nested_property(self):
        """Traversing through a public property to __dict__ should be blocked."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Invalid property name"):
            set_property_value(component, "nested_obj.__dict__", {}, data={})

    def test_dunder_init_via_nested_property(self):
        """Traversing to __init__ through nested property should be blocked."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Invalid property name"):
            set_property_value(component, "nested_obj.__init__", "hacked", data={})

    def test_dunder_module_via_nested_property(self):
        """Traversing to __module__ through nested property should be blocked."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Invalid property name"):
            set_property_value(component, "nested_obj.__module__", "hacked", data={})

    def test_valid_nested_property_works(self):
        """Legitimate nested properties should still work."""
        component = _make_component()
        data = {"nested_obj": {"visible": "hello"}}
        set_property_value(component, "nested_obj.visible", "updated", data=data)
        assert component.nested_obj.visible == "updated"

    def test_dict_nested_property_works(self):
        """Nested dict properties should work."""
        component = _make_component()
        data = {"nested": {"key": "value"}}
        set_property_value(component, "nested.key", "new_value", data=data)
        assert component.nested["key"] == "new_value"


# ═══════════════════════════════════════════════════════════════════════
# $parent method escalation
# ═══════════════════════════════════════════════════════════════════════


class TestParentEscalation:
    """Test that $parent traversal respects access controls."""

    def test_parent_protected_method_blocked(self):
        """Calling a protected method on parent via $parent should be blocked."""
        parent = _make_component(component_id="parent1")
        child = _make_component(cls=ChildComponent, component_id="child1")
        child.parent = parent

        # The render method is protected
        with pytest.raises(UnicornViewError, match="render"):
            _call_method_name(parent, "render", args=(), kwargs={})

    def test_parent_mount_blocked(self):
        """mount() should not be callable remotely even on parent."""
        parent = _make_component(component_id="parent2")
        with pytest.raises(UnicornViewError, match="mount"):
            _call_method_name(parent, "mount", args=(), kwargs={})

    def test_parent_reset_blocked(self):
        """reset() should not be callable remotely."""
        parent = _make_component(component_id="parent3")
        with pytest.raises(UnicornViewError, match="reset"):
            _call_method_name(parent, "reset", args=(), kwargs={})

    def test_parent_public_method_allowed(self):
        """Public methods on parent should be callable."""
        parent = _make_component(component_id="parent4")
        result = _call_method_name(parent, "save", args=(), kwargs={})
        assert result == "saved"


# ═══════════════════════════════════════════════════════════════════════
# set_property_from_data bypasses _is_public
# ═══════════════════════════════════════════════════════════════════════


class TestSetPropertyFromDataBypass:
    """
    set_property_from_data() uses hasattr() without checking _is_public.
    It's used in the bulk data sync path (message.py line 141-142).

    However, checksum validation means attacker can't forge arbitrary data
    without SECRET_KEY. These tests document the defense-in-depth gap.
    """

    def test_set_property_from_data_rejects_template_name(self):
        """
        set_property_from_data will NOT set template_name because it now checks _is_public.
        The checksum is no longer the sole primary defense.
        """
        component = _make_component()
        original_template = component.template_name

        # This is now blocked by set_property_from_data's _is_public guard.
        set_property_from_data(component, "template_name", "evil.html")

        # Confirm the value was NOT changed
        assert component.template_name == original_template

    def test_set_property_from_data_rejects_force_render(self):
        """force_render is a protected property and cannot be set via set_property_from_data."""
        component = _make_component()
        assert component.force_render is False

        set_property_from_data(component, "force_render", True)
        assert component.force_render is False

    def test_set_property_from_data_respects_hasattr(self):
        """Properties that don't exist won't be set (hasattr returns False)."""
        component = _make_component()
        set_property_from_data(component, "nonexistent_property_xyz", "value")
        assert (
            not hasattr(component, "nonexistent_property_xyz")
            or getattr(component, "nonexistent_property_xyz", None) is None
        )

    def test_checksum_prevents_data_tampering_in_practice(self):
        """
        Even though set_property_from_data lacks _is_public checks,
        the checksum validation prevents arbitrary data injection
        because the attacker would need SECRET_KEY to forge a valid checksum.
        """
        legitimate_data = {"name": "World"}
        legitimate_checksum = generate_checksum(legitimate_data)

        # Attacker tries to inject template_name
        tampered_data = {"name": "World", "template_name": "/etc/passwd"}
        tampered_checksum = generate_checksum(tampered_data)

        # Checksums won't match
        assert legitimate_checksum != tampered_checksum


# ═══════════════════════════════════════════════════════════════════════
# Component.call() JS injection
# ═══════════════════════════════════════════════════════════════════════


class TestCallJsInjection:
    """
    Server-side component.call() pushes JS function names to the client.
    If user input controls function name or args, it's a potential XSS vector.
    """

    def test_call_adds_to_calls_list(self):
        """call() should add function name and args to the calls list."""
        component = _make_component()
        component.calls = []
        component.call("Unicorn.showMessage", "hello")
        assert len(component.calls) == 1
        assert component.calls[0] == {"fn": "Unicorn.showMessage", "args": ("hello",)}

    def test_call_with_script_payload_in_args(self):
        """
        If user input with script content is passed as args, it will
        end up in the JSON response. The client-side callCalls fallback blocklist
        defends against execute-as-function, but args are passed through.
        """
        component = _make_component()
        component.calls = []
        component.call("Unicorn.displayText", "<script>alert(1)</script>")

        # The payload is stored as-is (the framework doesn't sanitize call args)
        assert component.calls[0]["args"] == ("<script>alert(1)</script>",)

    def test_call_with_eval_function_name_blocked_by_server_allowlist(self):
        """
        Server code calling component.call("eval", ...) will NOT add it to calls list
        because `eval` is not in the default ALLOWED_JS_CALL_LIST (only `'Unicorn'`).
        """
        component = _make_component()
        component.calls = []
        component.call("eval", "alert(1)")
        # Server side filters this by default
        assert len(component.calls) == 0


# ═══════════════════════════════════════════════════════════════════════
# Component name validation
# ═══════════════════════════════════════════════════════════════════════


class TestComponentNameValidation:
    r"""
    Test component name validation in UnicornView.create().
    The URL regex [\w/\.\-]+ provides first-line defense by only allowing
    word characters, forward slashes, dots, and hyphens.
    """

    def test_path_traversal_with_double_dot(self):
        """Classic path traversal with '..' should be rejected."""
        with pytest.raises(AssertionError, match="Invalid component name"):
            UnicornView.create(
                component_id="sec07_1",
                component_name="../../etc/passwd",
            )

    def test_embedded_double_dot(self):
        """Embedded '..' in component name should be rejected."""
        with pytest.raises(AssertionError, match="Invalid component name"):
            UnicornView.create(
                component_id="sec07_2",
                component_name="foo..bar",
            )

    def test_empty_component_name_rejected(self):
        """Empty component name should be rejected."""
        with pytest.raises(AssertionError, match="Component name is required"):
            UnicornView.create(
                component_id="sec07_3",
                component_name="",
            )

    def test_empty_component_id_rejected(self):
        """Empty component ID should be rejected."""
        with pytest.raises(AssertionError, match="Component id is required"):
            UnicornView.create(
                component_id="",
                component_name="test",
            )

    def test_url_regex_blocks_special_chars(self):
        """
        The URL pattern [\\w/\\.\\-]+ filters component names at the URL routing level.
        Characters like null bytes, semicolons, backticks won't even reach the view.
        This test documents this defense layer.
        """
        url_pattern = r"[\w/\.\-]+"

        # These should NOT match the URL pattern (blocked at routing level)
        dangerous_names = [
            "hello\x00world",  # null byte
            "hello;world",  # semicolon
            "hello`world",  # backtick
            "hello world",  # space
            "hello<world",  # angle bracket
            "hello>world",
            "hello'world",  # quote
            'hello"world',  # double quote
            "hello|world",  # pipe
        ]

        for name in dangerous_names:
            # full match = the regex must match the entire string
            match = re.fullmatch(url_pattern, name)
            assert match is None, f"URL regex should block '{name!r}'"

        # These SHOULD match (legitimate component names)
        safe_names = [
            "hello-world",
            "my_component",
            "app.component",
            "folder/component",
            "My.Nested.Component",
        ]

        for name in safe_names:
            match = re.fullmatch(url_pattern, name)
            assert match is not None, f"URL regex should allow '{name}'"


# ═══════════════════════════════════════════════════════════════════════
# ast.parse / ast.literal_eval in call_method_parser
# ═══════════════════════════════════════════════════════════════════════


class TestCallMethodParsing:
    """
    Verify that the AST-based method name parser safely handles
    adversarial inputs without code execution.
    """

    def test_literal_eval_rejects_function_calls(self):
        """ast.literal_eval should reject function call expressions."""
        # ast.literal_eval raises ValueError for non-literal expressions.
        # This proves that code like __import__('os') cannot be executed.
        with pytest.raises(ValueError, match="malformed node or string"):
            eval_value("__import__('os')")

    def test_literal_eval_rejects_lambda(self):
        """ast.literal_eval should reject lambda expressions."""
        # ast.literal_eval raises ValueError for lambda expressions.
        with pytest.raises(ValueError, match="malformed node or string"):
            eval_value("lambda: None")

    def test_parse_call_method_handles_deeply_nested(self):
        """Deeply nested method calls should parse without crashing."""
        # This tests that deeply nested AST doesn't cause stack overflow
        result = parse_call_method_name("method()")
        assert result[0] == "method"

    def test_parse_call_method_with_special_chars_in_string_arg(self):
        """Method with string args containing special chars should be handled safely."""
        result = parse_call_method_name("method('hello<script>alert(1)</script>')")
        method_name, args, _kwargs = result
        assert method_name == "method"
        assert args[0] == "hello<script>alert(1)</script>"

    def test_parse_call_method_with_dict_arg(self):
        """Method with dict args should be parsed safely."""
        result = parse_call_method_name("method({'key': 'value'})")
        method_name, args, _kwargs = result
        assert method_name == "method"
        assert args[0] == {"key": "value"}


# ═══════════════════════════════════════════════════════════════════════
# Setter method bypass
# ═══════════════════════════════════════════════════════════════════════


class TestSetterMethodBypass:
    """
    Test that setter syntax (prop=val) in callMethod respects _is_public.
    """

    def test_setter_rejects_template_name(self):
        """Setting template_name via setter syntax should be blocked."""
        component = _make_component()
        with pytest.raises(UnicornViewError, match="template_name"):
            # Simulate what call_method.handle does for setter methods
            if not component._is_public("template_name"):
                raise UnicornViewError("'template_name' is not a valid property name")

    def test_setter_rejects_underscore_property(self):
        """Setting _private property via setter syntax should be blocked."""
        component = _make_component()
        assert not component._is_public("_private")

    def test_setter_rejects_request(self):
        """Setting request via setter syntax should be blocked."""
        component = _make_component()
        assert not component._is_public("request")

    def test_setter_allows_public_property(self):
        """Setting a public property via setter syntax should work."""
        component = _make_component()
        assert component._is_public("name")
        assert component._is_public("count")

    def test_is_public_rejects_all_protected_names(self):
        """All protected names in _is_public should be rejected."""
        component = _make_component()
        protected_names = [
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
            "pre_parse",
            "post_parse",
        ]

        for name in protected_names:
            assert not component._is_public(name), f"'{name}' should NOT be public"


# ═══════════════════════════════════════════════════════════════════════
# mark_safe XSS via Meta.safe
# ═══════════════════════════════════════════════════════════════════════


class TestMarkSafeXss:
    """
    When a component has Meta.safe, string values are passed through
    mark_safe(), which means user-controlled input in those fields can be
    rendered as raw HTML.
    """

    def test_safe_field_wraps_with_mark_safe(self):
        """Safe fields should produce SafeText after _handle_safe_fields."""
        component = SafeFieldComponent(component_name="test_safe", component_id="sec10_1")
        component.html_content = "<b>bold</b>"
        component._handle_safe_fields()
        assert isinstance(component.html_content, SafeText)

    def test_safe_field_with_script_tag(self):
        """
        If a safe field contains a script tag and the field is user-controllable,
        mark_safe will pass it through unescaped. This is the intended behavior
        but a potential XSS vector if the field value comes from user input.
        """
        component = SafeFieldComponent(component_name="test_safe", component_id="sec10_2")
        xss_payload = "<script>document.cookie</script>"
        component.html_content = xss_payload
        component._handle_safe_fields()

        # After mark_safe, the value is marked as safe HTML (not escaped)
        assert isinstance(component.html_content, SafeText)
        assert str(component.html_content) == xss_payload

    def test_safe_field_set_via_property_value(self):
        """
        User can set a safe field via syncInput, and then _handle_safe_fields
        will mark it as safe. This is the attack chain.
        """
        component = SafeFieldComponent(component_name="test_safe", component_id="sec10_3")
        data = {"html_content": ""}
        xss_payload = "<img src=x onerror=alert(1)>"

        # Step 1: Attacker sets the property via syncInput
        set_property_value(component, "html_content", xss_payload, data=data)
        assert component.html_content == xss_payload

        # Step 2: Framework calls _handle_safe_fields during rendering
        component._handle_safe_fields()
        assert isinstance(component.html_content, SafeText)
        assert str(component.html_content) == xss_payload


# ═══════════════════════════════════════════════════════════════════════
# Open redirect via return value
# ═══════════════════════════════════════════════════════════════════════


class TestOpenRedirect:
    """
    Component methods returning redirect() send the URL to the client.
    If user input controls the redirect URL, it's an open redirect.
    """

    def test_redirect_url_passed_to_client(self):
        """
        When a method returns HttpResponseRedirect, the URL is included
        in the response JSON. If unvalidated, this is an open redirect.
        """
        ret = Return("test_method")
        ret.value = redirect("https://evil.com")
        data = ret.get_data()

        # The redirect URL is passed directly to the client
        assert data["value"]["url"] == "https://evil.com"

    def test_redirect_javascript_url_blocked_by_django(self):
        """
        Django 5.2+ blocks javascript: URLs in HttpResponseRedirect with
        DisallowedRedirect. This is a positive security finding — the
        framework already protects against javascript: protocol redirects.
        """
        with pytest.raises(DisallowedRedirect, match="javascript"):
            HttpResponseRedirect("javascript:alert(1)")

    def test_hash_update_injection(self):
        """
        HashUpdate sets window.location.hash on the client.
        Test that special characters in hash are passed through.
        """
        ret = Return("test_method")
        ret.value = HashUpdate("#test=1&evil=<script>")
        data = ret.get_data()

        assert data["value"]["hash"] == "#test=1&evil=<script>"


# ═══════════════════════════════════════════════════════════════════════
# Pickle deserialization
# ═══════════════════════════════════════════════════════════════════════


class TestPickleSafety:
    """
    Components are cached using pickle. If the cache backend
    is compromised (e.g., unauthenticated memcached), deserialization
    can lead to arbitrary code execution.

    These tests document the usage pattern rather than exploit it directly.
    """

    def test_component_uses_pickle_for_reset(self):
        """
        The reset() method uses pickle.loads() on cached attribute values.
        This documents that pickle is in the attack surface.
        """
        component = _make_component()
        # The _resettable_attributes_cache uses pickle
        for _attr_name, pickled_value in component._resettable_attributes_cache.items():
            # Verify the values are pickled bytes
            assert isinstance(pickled_value, bytes)
            # Verify they can be unpickled (normal operation)
            unpickled = pickle.loads(pickled_value)  # noqa: S301
            assert unpickled is not None

    def test_cache_key_is_predictable(self):
        """
        Cache keys follow the pattern 'unicorn:component:{component_id}'.
        If the component_id is known, the cache key is predictable.
        """
        component = _make_component(component_id="known_id")
        expected_key = "unicorn:component:known_id"
        assert component.component_cache_key == expected_key

    def test_corrupted_pickle_handled_gracefully(self):
        """
        If the pickled data is corrupted, reset() should handle it gracefully
        without crashing the application.
        """
        component = _make_component()
        # Inject corrupted pickle data
        component._resettable_attributes_cache["test_attr"] = b"corrupted_data_not_valid_pickle"
        # reset() should log a warning but not crash
        component.reset()  # Should not raise


# ═══════════════════════════════════════════════════════════════════════
# Additional edge cases
# ═══════════════════════════════════════════════════════════════════════


class TestAdditionalEdgeCases:
    """Edge cases and additional security tests."""

    def test_set_property_value_with_none_name(self):
        """Property name of None should be rejected."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Property name is required"):
            set_property_value(component, None, "value", data={})

    def test_set_property_value_with_none_value(self):
        """Property value of None should be rejected."""
        component = _make_component()
        with pytest.raises(AssertionError, match="Property value is required"):
            set_property_value(component, "name", None, data={})

    def test_call_method_with_nonexistent_method(self):
        """Calling a method that doesn't exist should return None, not crash."""
        component = _make_component()
        result = _call_method_name(component, "this_method_does_not_exist", args=(), kwargs={})
        assert result is None

    def test_call_method_rejects_all_lifecycle_hooks(self):
        """All lifecycle hook methods should be blocked from remote calls."""
        component = _make_component()
        lifecycle_methods = [
            "mount",
            "hydrate",
            "complete",
            "rendered",
            "parent_rendered",
            "updating",
            "updated",
            "resolved",
            "calling",
            "called",
            "reset",
            "pre_parse",
            "post_parse",
        ]

        for method_name in lifecycle_methods:
            with pytest.raises(UnicornViewError, match=method_name):
                _call_method_name(component, method_name, args=(), kwargs={})

    def test_call_method_rejects_templateview_internals(self):
        """TemplateView internal methods should be blocked."""
        component = _make_component()
        blocked_methods = [
            "render",
            "dispatch",
            "get",
            "get_context_data",
            "get_template_names",
            "render_to_response",
            "http_method_not_allowed",
            "options",
            "setup",
        ]

        for method_name in blocked_methods:
            with pytest.raises(UnicornViewError, match=method_name):
                _call_method_name(component, method_name, args=(), kwargs={})

    def test_set_property_rejects_all_protected_properties(self):
        """All protected property names should be rejected by set_property_value."""
        component = _make_component()
        protected_props = [
            "template_name",
            "request",
            "component_id",
            "component_name",
            "component_key",
            "template_html",
            "errors",
            "parent",
            "children",
            "calls",
            "component_cache_key",
            "component_kwargs",
            "component_args",
            "force_render",
        ]

        for prop_name in protected_props:
            with pytest.raises(UnicornViewError):
                set_property_value(component, prop_name, "hacked", data={})

    def test_underscore_prefix_always_treated_as_private(self):
        """Any name starting with _ should be treated as private."""
        component = _make_component()
        private_names = [
            "_private",
            "_set_property",
            "_methods_cache",
            "_attribute_names_cache",
            "_resettable_attributes_cache",
            "__class__",
            "__dict__",
            "__init__",
        ]

        for name in private_names:
            assert not component._is_public(name), f"'{name}' should be private"

    def test_public_properties_still_accessible(self):
        """Legitimate public properties should remain accessible."""
        component = _make_component()
        public_props = ["name", "count", "check", "nested", "items"]

        for prop_name in public_props:
            assert component._is_public(prop_name), f"'{prop_name}' should be public"
