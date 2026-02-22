import time

import shortuuid

from django_unicorn.components import UnicornView
from django_unicorn.components.unicorn_template_response import get_root_element
from django_unicorn.utils import generate_checksum


class FakeTargetComponent(UnicornView):
    template_name = "templates/test_component_target.html"

    clicked = False

    def test_method(self):
        self.clicked = True


def test_message_generated_checksum_matches_dom_checksum(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "target": None,
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()
    dom = body.get("dom")

    assert dom
    assert not body.get("partials")
    assert body.get("data", {}).get("clicked") is True

    root_element = get_root_element(dom)
    expected_meta = body.get("meta")

    if ":" in expected_meta:
        expected_meta = expected_meta.split(":")[0]

    actual_meta = root_element.attrib.get("unicorn:meta")
    assert actual_meta == expected_meta


def test_message_target_invalid(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "target": "test-target-id1",
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()

    assert body.get("dom")
    assert not body.get("partials")
    assert body.get("data", {}).get("clicked") is True


def test_message_target_id(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "partial": {"target": "test-target-id"},
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()

    assert body.get("dom") is None
    assert len(body["partials"]) == 1
    assert body["partials"][0]["id"] == "test-target-id"
    assert body["partials"][0]["dom"] == '<div id="test-target-id"></div>'
    assert body.get("data", {}).get("clicked") is True


def test_message_target_only_id(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "partial": {"id": "test-target-id"},
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()

    assert body.get("dom") is None
    assert len(body["partials"]) == 1
    assert body["partials"][0]["id"] == "test-target-id"
    assert body["partials"][0]["dom"] == '<div id="test-target-id"></div>'
    assert body.get("data", {}).get("clicked") is True


def test_message_target_only_key(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "partial": {"key": "test-target-key"},
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()

    assert body.get("dom") is None
    assert len(body["partials"]) == 1
    assert body["partials"][0]["key"] == "test-target-key"
    assert body["partials"][0]["dom"] == '<div unicorn:key="test-target-key"></div>'
    assert body.get("data", {}).get("clicked") is True


def test_message_target_key(client):
    data = {"clicked": False}
    message = {
        "actionQueue": [
            {
                "payload": {"name": "test_method"},
                "type": "callMethod",
                "partial": {"target": "test-target-key"},
            }
        ],
        "data": data,
        "meta": generate_checksum(str(data)),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
    }

    response = client.post(
        "/message/tests.views.message.test_target.FakeTargetComponent",
        message,
        content_type="application/json",
    )

    body = response.json()

    assert body.get("dom") is None
    assert len(body["partials"]) == 1
    assert body["partials"][0]["key"] == "test-target-key"
    assert body["partials"][0]["dom"] == '<div unicorn:key="test-target-key"></div>'
    assert body.get("data", {}).get("clicked") is True
