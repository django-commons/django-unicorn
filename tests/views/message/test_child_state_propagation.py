"""
Regression tests for issue #666: updating child components via a parent method.

When a parent component's method modifies children's state (e.g., setting
is_editing=True on all children), the changes must be persisted to cache before
the parent re-renders so that template tags retrieve the updated children.
"""

import shortuuid
from django.core.cache import caches
from tests.views.message.utils import post_and_get_response

from django_unicorn.cacher import cache_full_tree, restore_from_cache
from django_unicorn.components import UnicornView
from django_unicorn.settings import get_cache_alias


class ChildView(UnicornView):
    template_name = "templates/test_component.html"
    is_editing: bool = False


class ParentView(UnicornView):
    template_name = "templates/test_component.html"

    def begin_edit_all(self):
        for child in self.children:
            if hasattr(child, "is_editing"):
                child.is_editing = True


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
        assert cached.is_editing is True, (
            f"Child {child.component_id} should have is_editing=True after begin_edit_all"
        )
