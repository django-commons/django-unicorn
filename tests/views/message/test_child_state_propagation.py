"""
Regression tests for:
  - Issue #666: updating child components via a parent method.
  - Issue #685: self.parent reference not updating in child components.

When a parent component's method modifies children's state (e.g., setting
is_editing=True on all children), the changes must be persisted to cache before
the parent re-renders so that template tags retrieve the updated children.

Additionally, when children are rendered via template tags during a parent's
re-render, their self.parent must point to the exact in-memory parent object so
that they always see the parent's current state.
"""

import shortuuid
from django.core.cache import caches
from django.test import RequestFactory
from tests.views.message.utils import post_and_get_response

from django_unicorn.cacher import cache_full_tree
from django_unicorn.components import UnicornView
from django_unicorn.settings import get_cache_alias


class ChildView(UnicornView):
    template_name = "templates/test_component.html"
    is_editing: bool = False


class ParentView(UnicornView):
    template_name = "templates/test_component.html"
    current_page: str = "root"

    def begin_edit_all(self):
        for child in self.children:
            if hasattr(child, "is_editing"):
                child.is_editing = True

    def walk(self, page: str):
        self.current_page = page


PARENT_NAME = "tests.views.message.test_child_state_propagation.ParentView"
CHILD_NAME = "tests.views.message.test_child_state_propagation.ChildView"


def test_parent_method_child_state_persisted_in_cache(client):
    """
    When a parent method modifies child component state, those changes must be
    saved to the Django cache before the parent renders. Without the fix, the
    child's is_editing remains False in the cache even after begin_edit_all runs.
    """
    parent_id = shortuuid.uuid()[:8]
    child_id = f"{parent_id}:{CHILD_NAME}"

    parent = ParentView(component_id=parent_id, component_name=PARENT_NAME)
    child = ChildView(component_id=child_id, component_name=CHILD_NAME, parent=parent)

    assert child.is_editing is False

    # Populate Django cache with initial state
    cache_full_tree(parent)

    # Verify initial cache state
    cache = caches[get_cache_alias()]
    cached_child_before = cache.get(child.component_cache_key)
    assert cached_child_before is not None
    assert cached_child_before.is_editing is False

    # Call the parent method that modifies all children
    post_and_get_response(
        client,
        url=f"/message/{PARENT_NAME}",
        data={},
        action_queue=[
            {
                "payload": {"name": "begin_edit_all"},
                "type": "callMethod",
            }
        ],
        component_id=parent_id,
    )

    # After the method runs, the child should be in cache with is_editing=True
    cached_child_after = cache.get(child.component_cache_key)
    assert cached_child_after is not None, "Child should still be in cache"
    assert cached_child_after.is_editing is True, (
        "Child's is_editing should be True after parent's begin_edit_all. "
        "If False, cache_full_tree was not called before rendering."
    )


def test_child_self_parent_is_in_memory_parent_after_create():
    """
    Issue #685: when UnicornView.create() returns a cached child component,
    its self.parent must be the *exact same Python object* as the in-memory parent
    being rendered, not a stale copy restored from the Django cache.

    We verify this by calling create() with an updated in-memory parent and
    checking that the returned child's .parent IS that same object.
    """
    parent_id = shortuuid.uuid()[:8]
    child_id = f"{parent_id}:{CHILD_NAME}"

    parent = ParentView(component_id=parent_id, component_name=PARENT_NAME)
    child = ChildView(component_id=child_id, component_name=CHILD_NAME, parent=parent)

    # Persist to cache (simulates initial page load state)
    cache_full_tree(parent)

    # Simulate the parent changing state (e.g. walk() was called)
    parent.current_page = "chapter-2"

    request = RequestFactory().get("/")

    # When the parent template re-renders, the template tag calls create() for the child
    retrieved_child = UnicornView.create(
        component_id=child_id,
        component_name=CHILD_NAME,
        parent=parent,
        request=request,
    )

    assert retrieved_child.parent is parent, (
        "self.parent in the child should be the exact in-memory parent object, "
        "not a stale cache-restored copy (issue #685)."
    )
    assert retrieved_child.parent.current_page == "chapter-2", (
        "self.parent.current_page should reflect the parent's current in-memory state."
    )


def test_parent_method_multiple_children_all_updated_in_cache(client):
    """
    All children must be updated in cache, not just the first one.
    """
    parent_id = shortuuid.uuid()[:8]
    child_id_1 = f"{parent_id}:{CHILD_NAME}:1"
    child_id_2 = f"{parent_id}:{CHILD_NAME}:2"
    child_id_3 = f"{parent_id}:{CHILD_NAME}:3"

    parent = ParentView(component_id=parent_id, component_name=PARENT_NAME)
    child1 = ChildView(component_id=child_id_1, component_name=CHILD_NAME, parent=parent)
    child2 = ChildView(component_id=child_id_2, component_name=CHILD_NAME, parent=parent)
    child3 = ChildView(component_id=child_id_3, component_name=CHILD_NAME, parent=parent)

    cache_full_tree(parent)

    cache = caches[get_cache_alias()]
    for child in [child1, child2, child3]:
        assert cache.get(child.component_cache_key).is_editing is False

    post_and_get_response(
        client,
        url=f"/message/{PARENT_NAME}",
        data={},
        action_queue=[
            {
                "payload": {"name": "begin_edit_all"},
                "type": "callMethod",
            }
        ],
        component_id=parent_id,
    )

    for child in [child1, child2, child3]:
        cached = cache.get(child.component_cache_key)
        assert cached is not None
        assert cached.is_editing is True, f"Child {child.component_id} should have is_editing=True after begin_edit_all"
