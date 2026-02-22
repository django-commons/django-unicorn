import time

import orjson
import shortuuid

from django_unicorn.utils import generate_checksum


def _post_message_and_get_body(client, message):
    response = client.post(
        "/message/tests.views.fake_components.FakeComponent",
        message,
        content_type="application/json",
    )

    body = orjson.loads(response.content)
    return body


def test_message_toggle(client):
    data = {"check": False}
    message = {
        "actionQueue": [
            {"type": "callMethod", "payload": {"name": "$toggle('check')"}},
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(client, message)

    assert not body["errors"]
    assert body["data"]["check"] is True


def test_message_nested_toggle(client):
    data = {"nested": {"check": False}}
    message = {
        "actionQueue": [
            {"type": "callMethod", "payload": {"name": "$toggle('nested.check')"}},
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    body = _post_message_and_get_body(client, message)

    assert not body["errors"]
    assert body["data"]["nested"]["check"] is True
