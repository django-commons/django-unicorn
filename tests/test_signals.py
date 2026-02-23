"""
Tests for django_unicorn.signals verifies that each Django signal fires with
the expected kwargs at the correct point in the component lifecycle.
"""

import shortuuid
from django.test import Client, RequestFactory

from django_unicorn.components import UnicornView
from django_unicorn.signals import (
    component_completed,
    component_hydrated,
    component_method_called,
    component_method_calling,
    component_mounted,
    component_post_parsed,
    component_pre_parsed,
    component_property_updated,
    component_property_updating,
    component_rendered,
)
from tests.views.message.utils import post_and_get_response

FAKE_COMPONENT = "tests.views.fake_components.FakeComponent"
FAKE_URL = f"/message/{FAKE_COMPONENT}"


def _collect(signal):
    """Return a (received_list, handler) pair.  Caller must disconnect handler."""
    received = []

    def handler(sender, **kwargs):
        received.append({"sender": sender, **kwargs})

    signal.connect(handler)
    return received, handler


def test_component_mounted_signal():
    """component_mounted fires when a component is first constructed."""
    received, handler = _collect(component_mounted)
    try:
        request = RequestFactory().get("/")
        component_id = shortuuid.uuid()[:8]
        UnicornView.create(
            component_id=component_id,
            component_name=FAKE_COMPONENT,
            request=request,
            use_cache=False,
        )
    finally:
        component_mounted.disconnect(handler)

    assert len(received) >= 1
    last = received[-1]
    assert last["sender"].__name__ == "FakeComponent"
    assert last["component"].component_name == FAKE_COMPONENT


def test_component_hydrated_signal():
    """component_hydrated fires when a component's data is hydrated."""
    received, handler = _collect(component_hydrated)
    try:
        request = RequestFactory().get("/")
        UnicornView.create(
            component_id=shortuuid.uuid()[:8],
            component_name=FAKE_COMPONENT,
            request=request,
            use_cache=False,
        )
    finally:
        component_hydrated.disconnect(handler)

    assert len(received) >= 1
    assert received[-1]["component"].component_name == FAKE_COMPONENT


def test_component_completed_signal():
    """component_completed fires after all actions are processed."""
    received, handler = _collect(component_completed)
    try:
        request = RequestFactory().get("/")
        UnicornView.create(
            component_id=shortuuid.uuid()[:8],
            component_name=FAKE_COMPONENT,
            request=request,
            use_cache=False,
        )
    finally:
        component_completed.disconnect(handler)

    assert len(received) >= 1


def test_component_pre_and_post_parsed_signals(client):
    """component_pre_parsed and component_post_parsed fire on every AJAX request."""
    pre_received, pre_handler = _collect(component_pre_parsed)
    post_received, post_handler = _collect(component_post_parsed)
    try:
        post_and_get_response(
            client,
            url=FAKE_URL,
            data={"method_count": 0},
            action_queue=[{"payload": {"name": "test_method"}, "type": "callMethod"}],
        )
    finally:
        component_pre_parsed.disconnect(pre_handler)
        component_post_parsed.disconnect(post_handler)

    assert len(pre_received) >= 1
    assert len(post_received) >= 1


def test_component_method_calling_signal(client):
    """component_method_calling fires before a method is invoked."""
    received, handler = _collect(component_method_calling)
    try:
        post_and_get_response(
            client,
            url=FAKE_URL,
            data={"method_count": 0},
            action_queue=[{"payload": {"name": "test_method"}, "type": "callMethod"}],
        )
    finally:
        component_method_calling.disconnect(handler)

    assert len(received) >= 1
    last = received[-1]
    assert last["name"] == "test_method"
    assert isinstance(last["args"], tuple | list)


def test_component_method_called_signal_success(client):
    """component_method_called fires after a method succeeds with success=True."""
    received, handler = _collect(component_method_called)
    try:
        post_and_get_response(
            client,
            url=FAKE_URL,
            data={"method_count": 0},
            action_queue=[{"payload": {"name": "test_method"}, "type": "callMethod"}],
        )
    finally:
        component_method_called.disconnect(handler)

    assert len(received) >= 1
    last = received[-1]
    assert last["method_name"] == "test_method"
    assert last["success"] is True
    assert last["error"] is None
    assert "result" in last


class _FailComponent(UnicornView):
    template_name = "templates/test_component.html"

    def boom(self):
        raise ValueError("kaboom")


_FAIL_NAME = "tests.test_signals._FailComponent"
_FAIL_URL = f"/message/{_FAIL_NAME}"


def test_component_method_called_signal_failure():
    """component_method_called fires even when a method raises, with success=False."""
    received, handler = _collect(component_method_called)
    no_raise_client = Client(raise_request_exception=False)
    try:
        post_and_get_response(
            no_raise_client,
            url=_FAIL_URL,
            data={},
            action_queue=[{"payload": {"name": "boom"}, "type": "callMethod"}],
            return_response=True,
        )
    finally:
        component_method_called.disconnect(handler)

    failure_signals = [r for r in received if r.get("success") is False]
    assert len(failure_signals) >= 1
    last = failure_signals[-1]
    assert last["method_name"] == "boom"
    assert last["result"] is None
    assert isinstance(last["error"], ValueError)


def test_component_rendered_signal(client):
    """component_rendered fires after a component re-renders on an AJAX request."""
    received, handler = _collect(component_rendered)
    try:
        post_and_get_response(
            client,
            url=FAKE_URL,
            data={"method_count": 0},
            action_queue=[{"payload": {"name": "test_method"}, "type": "callMethod"}],
        )
    finally:
        component_rendered.disconnect(handler)

    assert len(received) >= 1
    last = received[-1]
    assert "html" in last
    assert isinstance(last["html"], str)
    assert len(last["html"]) > 0


def test_component_property_updating_and_updated_signals(client):
    """Both property signals fire when a syncInput action updates a field."""
    updating_received, updating_handler = _collect(component_property_updating)
    updated_received, updated_handler = _collect(component_property_updated)
    try:
        post_and_get_response(
            client,
            url=FAKE_URL,
            data={"method_count": 0},
            action_queue=[
                {
                    "payload": {"name": "method_count", "value": 5},
                    "type": "syncInput",
                }
            ],
        )
    finally:
        component_property_updating.disconnect(updating_handler)
        component_property_updated.disconnect(updated_handler)

    assert len(updating_received) >= 1
    assert len(updated_received) >= 1

    updating_entry = next(r for r in updating_received if r["name"] == "method_count")
    assert updating_entry["value"] == 5

    updated_entry = next(r for r in updated_received if r["name"] == "method_count")
    assert updated_entry["value"] == 5
