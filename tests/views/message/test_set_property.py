import time

import orjson
import shortuuid

from django_unicorn.utils import generate_checksum


def _post_message_and_get_body(client, message, url="/message/tests.views.fake_components.FakeComponent"):
    response = client.post(
        url,
        message,
        content_type="application/json",
    )

    body = orjson.loads(response.content)
    return body


def test_setter(client):
    data = {"nested": {"check": False}, "check": False}
    message = {
        "actionQueue": [
            {"type": "callMethod", "payload": {"name": "check=True"}},
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(client, message)

    assert not body["errors"]
    assert body["data"]["check"] is True


def test_setter_updated(client):
    data = {"count": 1}
    message = {
        "actionQueue": [
            {"type": "callMethod", "payload": {"name": "count=2"}},
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(
        client,
        message,
        url="/message/tests.views.fake_components.FakeComponentWithUpdateMethods",
    )

    assert not body["errors"]
    assert body["data"]["count"] == 2

    # If updating_count or updated_count is called more than once
    # `FakeComponentWithUpdateMethods` will raise an exception


def test_setter_resolved(client):
    data = {"count": 1}
    action_queue = [
        {"type": "syncInput", "payload": {"name": "count", "value": 2}, "partials": []},
        {"type": "syncInput", "payload": {"name": "count", "value": 3}, "partials": []},
    ]
    message = {
        "actionQueue": action_queue,
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(
        client,
        message,
        url="/message/tests.views.fake_components.FakeComponentWithResolveMethods",
    )

    assert not body["errors"]
    assert body["data"]["count"] == 3

    # If resolved_count is called more than once `FakeComponentWithResolveMethods` will raise an exception


def test_nested_setter(client):
    data = {"nested": {"check": False}}
    message = {
        "actionQueue": [
            {"type": "callMethod", "payload": {"name": "nested.check=True"}},
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(client, message)

    assert not body["errors"]
    assert body["data"]["nested"]["check"] is True


def test_equal_sign(client):
    data = {"nested": {"check": False}, "method_arg": ""}
    message = {
        "actionQueue": [
            {
                "type": "callMethod",
                "payload": {"name": "test_method_string_arg('does=thiswork?')"},
            },
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(client, message)

    assert not body["errors"]
    assert body["data"]["method_arg"] == "does=thiswork?"
