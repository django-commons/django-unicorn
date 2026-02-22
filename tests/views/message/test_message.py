import time
from uuid import uuid4

import pytest
from django.http import JsonResponse

from django_unicorn.errors import ComponentClassLoadError, ComponentModuleLoadError
from django_unicorn.views import message


def assert_json_error(response, error):
    assert isinstance(response, JsonResponse)
    assert response.status_code == 200
    assert response.json().get("error") == error


def post_json(client, data, url="/message/test-message"):
    return client.post(url, data, content_type="application/json")


def test_view_csrf(rf):
    request = rf.post("/message/test-message-csrf")
    response = message(request)
    assert response.status_code == 403


def test_message_component_name_is_none(client):
    response = client.post("/message")

    assert_json_error(response, "Missing component name in url")


def test_message_no_body(client):
    response = client.post("/message/test-message-no-body")

    assert_json_error(response, "Body could not be parsed")


def test_message_no_data(client):
    data = {}
    response = post_json(client, data)

    assert_json_error(response, "Invalid JSON body")


def test_message_no_meta(client):
    data = {
        "data": {},
        "id": str(uuid4()),
        "epoch": time.time(),
    }
    response = post_json(client, data, url="/message/test-message-no-checksum")

    assert_json_error(response, "Missing meta")


def test_message_bad_meta(client):
    data = {
        "data": {},
        "meta": "asdf",
        "id": str(uuid4()),
        "epoch": time.time(),
    }
    response = post_json(client, data, url="/message/test-message-bad-checksum")

    assert_json_error(response, "Checksum does not match")


def test_message_no_component_id(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "epoch": time.time(),
    }
    response = post_json(client, data, url="/message/test-message-no-component-id")

    assert_json_error(response, "Missing component id")


def test_message_no_epoch(client):
    data = {"data": {}, "meta": "DVVk97cx", "id": str(uuid4())}
    response = post_json(client, data, url="/message/test-message-no-epoch")

    assert_json_error(response, "Missing epoch")


def test_message_component_module_not_loaded(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "id": str(uuid4()),
        "epoch": time.time(),
    }

    with pytest.raises(ComponentModuleLoadError) as e:
        post_json(client, data, url="/message/test-message-module-not-loaded")

    assert (
        e.exconly()
        == "django_unicorn.errors.ComponentModuleLoadError: The component module 'test_message_module_not_loaded' could not be loaded."  # noqa: E501
    )
    assert e.value.locations == [
        ("unicorn.components.test_message_module_not_loaded", "TestMessageModuleNotLoadedView"),
        ("components.test_message_module_not_loaded", "TestMessageModuleNotLoadedView"),
    ]


def test_message_component_class_not_loaded(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "id": str(uuid4()),
        "epoch": time.time(),
    }

    with pytest.raises(ComponentClassLoadError) as e:
        post_json(
            client,
            data,
            url="/message/tests.views.fake_components.FakeComponentNotThere",
        )

    expected_exception_message = "django_unicorn.errors.ComponentClassLoadError: The component class \
'tests.views.fake_components.FakeComponentNotThere' could not be loaded: module 'tests.views.fake_components' \
has no attribute 'FakeComponentNotThere'"

    assert e.exconly() == expected_exception_message

    expected_locations = [
        ("tests.views.fake_components", "FakeComponentNotThere"),
        (
            "unicorn.components.tests.views.fake_components.FakeComponentNotThere",
            "FakecomponentnotthereView",
        ),
        (
            "components.tests.views.fake_components.FakeComponentNotThere",
            "FakecomponentnotthereView",
        ),
    ]
    assert e.value.locations == expected_locations


def test_message_component_class_with_attribute_error(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "id": str(uuid4()),
        "epoch": time.time(),
    }

    with pytest.raises(ComponentClassLoadError) as e:
        post_json(
            client,
            data,
            url="/message/tests.views.fake_components.FakeComponentWithError",
        )

    assert e.value.__cause__


def test_message_component_with_dash(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "id": str(uuid4()),
        "epoch": time.time(),
    }

    with pytest.raises(ComponentModuleLoadError) as e:
        post_json(client, data, url="/message/test-with-dash")

    assert (
        e.exconly()
        == "django_unicorn.errors.ComponentModuleLoadError: The component module 'test_with_dash' could not be loaded."
    )


def test_message_component_with_dot(client):
    data = {
        "data": {},
        "meta": "DVVk97cx",
        "id": str(uuid4()),
        "epoch": time.time(),
    }

    with pytest.raises(ComponentClassLoadError) as e:
        post_json(client, data, url="/message/test.dot")

    expected = "django_unicorn.errors.ComponentClassLoadError: The component class 'test.dot' could not be loaded: \
module 'test' has no attribute 'dot'"
    actual = e.exconly()

    assert actual == expected
