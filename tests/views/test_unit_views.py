import json
from unittest.mock import Mock

import pytest

from django_unicorn.components import Component
from django_unicorn.errors import RenderNotModifiedError
from django_unicorn.utils import generate_checksum
from django_unicorn.views.action import CallMethod, Refresh, SyncInput, Toggle
from django_unicorn.views.request import ComponentRequest
from django_unicorn.views.response import ComponentResponse


def test_action_sync_input():
    data = {"type": "syncInput", "payload": {"name": "foo", "value": "bar"}}
    action = SyncInput(data)
    assert action.name == "foo"
    assert action.value == "bar"


def test_action_call_method():
    data = {"type": "callMethod", "payload": {"name": "foo(1, a=2)"}}
    action = CallMethod(data)
    assert action.method_name == "foo"
    assert action.args == (1,)
    assert action.kwargs == {"a": 2}


def test_action_toggle():
    data = {"type": "callMethod", "payload": {"name": "$toggle('foo')"}}
    action = Toggle(data)
    assert action.method_name == "$toggle"
    assert action.args == ("foo",)


def test_component_request_parsing():
    request = Mock()
    body = {
        "id": "123",
        "name": "test-component",
        "epoch": 123456,
        "key": "",
        "hash": "abc",
        "data": {},
        "meta": "fail",
    }

    body["meta"] = generate_checksum(str(body["data"]))

    request.body = json.dumps(body).encode("utf-8")

    req = ComponentRequest(request, "test-component")
    assert req.id == "123"
    assert req.name == "test-component"
    assert req.data == {}


def test_component_request_action_parsing():
    request = Mock()
    body = {
        "id": "123",
        "name": "test-component",
        "epoch": 123456,
        "key": "",
        "hash": "abc",
        "data": {},
        "actionQueue": [
            {"type": "syncInput", "payload": {"name": "foo", "value": "bar"}},
            {"type": "callMethod", "payload": {"name": "$refresh"}},
            {"type": "callMethod", "payload": {"name": "foo"}},
        ],
    }

    body["meta"] = generate_checksum(str(body["data"]))
    request.body = json.dumps(body).encode("utf-8")

    req = ComponentRequest(request, "test-component")
    assert len(req.action_queue) == 3
    assert isinstance(req.action_queue[0], SyncInput)

    assert isinstance(req.action_queue[1], Refresh)
    assert isinstance(req.action_queue[2], CallMethod)


def test_component_response_structure():
    component = Mock(spec=Component)
    component.errors = {}
    component.calls = []
    component.children = []
    component.parent = None
    component.force_render = False

    # Mock render result
    component.render.return_value = "<div></div>"
    component.last_rendered_dom = "<div></div>"

    req = Mock(spec=ComponentRequest)
    req.id = "123"
    req.data = {}
    req.hash = "123"

    # We expect RenderNotModifiedError if hash matches and valid
    # But ComponentResponse assumes processing is done.

    # Calculate real checksum

    req.hash = generate_checksum(component.last_rendered_dom)

    with pytest.raises(RenderNotModifiedError):
        res = ComponentResponse(component, req)
        res.get_data()

    # If hash differs
    req.hash = "different"
    res = ComponentResponse(component, req)
    data = res.get_data()
    assert data["id"] == "123"
    assert "dom" in data
