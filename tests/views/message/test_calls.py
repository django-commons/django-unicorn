from tests.views.message.utils import post_and_get_response

from django_unicorn.components import UnicornView


class FakeCallsComponent(UnicornView):
    template_name = "templates/test_component.html"

    def test_call(self):
        self.call("testCall")

    def test_call2(self):
        self.call("testCall2")

    def test_call3(self):
        self.call("testCall3", "hello")

    def test_remove(self):
        self.remove()


FAKE_CALLS_COMPONENT_URL = "/message/tests.views.message.test_calls.FakeCallsComponent"


def test_message_calls(client):
    action_queue = [
        {
            "payload": {"name": "test_call"},
            "type": "callMethod",
            "target": None,
        }
    ]

    response = post_and_get_response(client, url=FAKE_CALLS_COMPONENT_URL, action_queue=action_queue)

    assert response.get("calls") == [{"args": [], "fn": "testCall"}]


def test_message_multiple_calls(client):
    action_queue = [
        {
            "payload": {"name": "test_call"},
            "type": "callMethod",
            "target": None,
        },
        {
            "payload": {"name": "test_call2"},
            "type": "callMethod",
            "target": None,
        },
    ]
    response = post_and_get_response(client, url=FAKE_CALLS_COMPONENT_URL, action_queue=action_queue)

    assert response.get("calls") == [
        {"args": [], "fn": "testCall"},
        {"args": [], "fn": "testCall2"},
    ]


def test_message_calls_with_arg(client):
    action_queue = [
        {
            "payload": {"name": "test_call3"},
            "type": "callMethod",
            "target": None,
        }
    ]

    response = post_and_get_response(client, url=FAKE_CALLS_COMPONENT_URL, action_queue=action_queue)

    assert response.get("calls") == [{"args": ["hello"], "fn": "testCall3"}]


def test_message_remove(client):
    component_id = "test-remove-id"
    action_queue = [
        {
            "payload": {"name": "test_remove"},
            "type": "callMethod",
            "target": None,
        }
    ]

    response = post_and_get_response(
        client, url=FAKE_CALLS_COMPONENT_URL, action_queue=action_queue, component_id=component_id
    )

    assert response.get("calls") == [{"args": [component_id], "fn": "Unicorn.deleteComponent"}]


class FakeChildComponent(UnicornView):
    template_name = "templates/test_component.html"

    def child_method(self):
        self.call("createChart", {"data": "test"})


class FakeParentComponent(UnicornView):
    template_name = "templates/test_component.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create a child component
        child = FakeChildComponent(component_name="fake-child", id="child-123")
        child.parent = self
        self.children.append(child)

    def call_child_method(self):
        # Parent calls child's method
        for child in self.children:
            if hasattr(child, "child_method") and callable(child.child_method):
                child.child_method()  # type: ignore[call-top-callable]


FAKE_PARENT_COMPONENT_URL = "/message/tests.views.message.test_calls.FakeParentComponent"


def test_message_child_calls_from_parent(client):
    """Test that child component calls are included when parent calls child method."""
    action_queue = [
        {
            "payload": {"name": "call_child_method"},
            "type": "callMethod",
            "target": None,
        }
    ]

    response = post_and_get_response(client, url=FAKE_PARENT_COMPONENT_URL, action_queue=action_queue)

    # Verify child's JavaScript call is in the response
    calls = response.get("calls", [])
    assert any(call["fn"] == "createChart" for call in calls), f"Expected 'createChart' in calls, got: {calls}"
    assert len(calls) == 1
    assert calls[0]["args"] == [{"data": "test"}]


class FakeGrandchildComponent(UnicornView):
    template_name = "templates/test_component.html"

    def grandchild_method(self):
        self.call("grandchildFunction", "nested")


class FakeChildWithGrandchildComponent(UnicornView):
    template_name = "templates/test_component.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create a grandchild component
        grandchild = FakeGrandchildComponent(component_name="fake-grandchild", id="grandchild-456")
        grandchild.parent = self
        self.children.append(grandchild)

    def child_method_with_call(self):
        self.call("childFunction")
        # Also call grandchild's method
        for child in self.children:
            if hasattr(child, "grandchild_method") and callable(child.grandchild_method):
                child.grandchild_method()  # type: ignore[call-top-callable]


class FakeParentWithNestedChildren(UnicornView):
    template_name = "templates/test_component.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create a child component with its own child
        child = FakeChildWithGrandchildComponent(component_name="fake-child-nested", id="child-nested-789")
        child.parent = self
        self.children.append(child)

    def call_nested_children(self):
        self.call("parentFunction")
        # Call child's method which will also call grandchild
        for child in self.children:
            if hasattr(child, "child_method_with_call") and callable(child.child_method_with_call):
                child.child_method_with_call()  # type: ignore[call-top-callable]


FAKE_NESTED_COMPONENT_URL = "/message/tests.views.message.test_calls.FakeParentWithNestedChildren"


def test_message_nested_child_calls(client):
    """Test that grandchild component calls are included in deeply nested scenarios."""
    action_queue = [
        {
            "payload": {"name": "call_nested_children"},
            "type": "callMethod",
            "target": None,
        }
    ]

    response = post_and_get_response(client, url=FAKE_NESTED_COMPONENT_URL, action_queue=action_queue)

    # Verify all levels of calls are collected: parent, child, and grandchild
    calls = response.get("calls", [])
    call_functions = [call["fn"] for call in calls]

    assert "parentFunction" in call_functions, f"Expected 'parentFunction' in calls, got: {call_functions}"
    assert "childFunction" in call_functions, f"Expected 'childFunction' in calls, got: {call_functions}"
    assert "grandchildFunction" in call_functions, f"Expected 'grandchildFunction' in calls, got: {call_functions}"
    assert len(calls) == 3
