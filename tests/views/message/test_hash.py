import shortuuid
from tests.views.fake_components import FakeComponent
from tests.views.message.test_calls import FakeCallsComponent
from tests.views.message.utils import post_and_get_response

from django_unicorn.components import UnicornView
from django_unicorn.components.unicorn_template_response import get_root_element
from django_unicorn.utils import generate_checksum, html_element_to_string


class FakeComponentParent(UnicornView):
    template_name = "templates/test_component_parent.html"

    value: int = 0


class FakeComponentParentWithValue(UnicornView):
    template_name = "templates/test_component_parent_with_value.html"

    value: int = 0


class FakeComponentChild(UnicornView):
    template_name = "templates/test_component_child.html"

    def parent_increment(self):
        self.parent.value += 1  # type: ignore


def test_message_hash_no_change(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_method_kwargs(count=0)"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    assert response.status_code == 304


def test_message_hash_changes(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_method_kwargs(count=1)"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    assert response["data"]["method_count"] == 1


def test_message_hash_no_change_but_return_value(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_return_value"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response["return"]["value"]


def test_message_hash_no_change_but_return_redirect(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_redirect"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response["return"]["value"]


def test_message_hash_no_change_but_return_hash_update(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_hash_update"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response["return"]["value"]


def test_message_hash_no_change_but_return_poll_update(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_poll_update"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response["return"]["value"]


def test_message_hash_no_change_but_return_location_update(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponent(
        component_id=component_id,
        component_name="tests.views.fake_components.FakeComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {"method_count": 0}
    response = post_and_get_response(
        client,
        url="/message/tests.views.fake_components.FakeComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_refresh_redirect"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response["return"]["value"]


def test_message_hash_no_change_but_calls(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeCallsComponent(
        component_id=component_id,
        component_name="tests.views.message.test_calls.FakeCallsComponent",
    )
    rendered_content = component.render()
    root_element = get_root_element(rendered_content)
    root_element.attrib.pop("unicorn:meta", None)
    meta = generate_checksum(html_element_to_string(root_element))

    data = {}
    response = post_and_get_response(
        client,
        url="/message/tests.views.message.test_calls.FakeCallsComponent",
        data=data,
        action_queue=[
            {
                "payload": {"name": "test_call"},
                "type": "callMethod",
            }
        ],
        component_id=component_id,
        hash=meta,
    )

    # check that the response is JSON and not a 304
    assert isinstance(response, dict)
    assert response.get("calls") == [{"args": [], "fn": "testCall"}]


def test_message_hash_no_change_but_parent(client):
    component_id = shortuuid.uuid()[:8]
    component = FakeComponentParentWithValue(
        component_id=component_id,
        component_name="tests.views.message.test_hash.FakeComponentParentWithValue",
    )
    component.render()

    assert component.value == 0

    child = component.children[0]
    rendered_child_content = child.render()
    child_hash = generate_checksum(rendered_child_content)

    assert child.parent.value == 0  # type: ignore

    data = {}
    response = post_and_get_response(
        client,
        url="/message/tests.views.message.test_hash.FakeComponentChild",
        data=data,
        action_queue=[
            {
                "payload": {"name": "parent_increment()"},
                "type": "callMethod",
            }
        ],
        component_id=child.component_id,
        hash=child_hash,
        return_response=True,
    )

    assert response.status_code == 200

    # TODO: Revisit this assert after child upgrade
    # assert child.parent.value == 1

    # rendered_parent_content = child.parent.render()
    # assert "||value:1||" in rendered_parent_content
