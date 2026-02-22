import shortuuid
from tests.views.message.utils import post_and_get_response

from django_unicorn.cacher import cache_full_tree
from django_unicorn.components import UnicornView


class NestedMethodCallParentView(UnicornView):
    template_name = "templates/test_component.html"
    count = 0

    def increment(self):
        self.count += 1


class NestedMethodCallChildView(UnicornView):
    template_name = "templates/test_component.html"


def test_nested_method_call_on_parent(client):
    """
    Test that calling a method on a parent component (e.g. $parent.increment()) works correctly
    and doesn't raise an AttributeError.
    """
    parent_id = shortuuid.uuid()[:8]
    # We need to use the full path to the component class so Unicorn can instantiate it
    parent_name = "tests.views.message.test_nested_method_call.NestedMethodCallParentView"
    parent = NestedMethodCallParentView(component_id=parent_id, component_name=parent_name)

    child_id = shortuuid.uuid()[:8]
    child_name = "tests.views.message.test_nested_method_call.NestedMethodCallChildView"
    child = NestedMethodCallChildView(component_id=child_id, component_name=child_name, parent=parent)

    # Manually cache the parent so the child can find it during the message request
    cache_full_tree(parent)

    data = {}
    action_queue = [
        {
            "payload": {"name": "$parent.increment()"},
            "type": "callMethod",
        }
    ]

    # This should not raise AttributeError: 'Attribute' object has no attribute 'id'
    response = post_and_get_response(
        client,
        url=f"/message/{child_name}",
        data=data,
        action_queue=action_queue,
        component_id=child_id,
    )

    assert not response.get("error")
    # The parent should be in the response because force_render was set to True in call_method.handle
    assert "parent" in response
    assert response["parent"]["data"]["count"] == 1
