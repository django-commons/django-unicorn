from unittest.mock import MagicMock, patch

import pytest
from django import forms

from django_unicorn.cacher import (
    CacheableComponent,
    PointerUnicornView,
    cache_full_tree,
    restore_from_cache,
)
from django_unicorn.components import UnicornView
from django_unicorn.errors import UnicornCacheError


class FakeComponent(UnicornView):
    pass


class FakeComponentWithTemplateHtml(UnicornView):
    template_html = """<div>
    testing
</div>
"""


def test_cacheable_component_request_is_none_then_restored():
    component = FakeComponent(
        component_id="test_cacheable_component_request_is_none_then_restored", component_name="hello-world"
    )
    request = component.request = MagicMock()
    assert component.request

    with CacheableComponent(component):
        assert component.request is None

    assert component.request == request


def test_cacheable_component_extra_context_is_none_then_restored():
    component = FakeComponent(
        component_id="test_cacheable_component_extra_context_is_none_then_restored", component_name="hello-world"
    )
    extra_context = component.extra_context = MagicMock()
    assert component.extra_context

    with CacheableComponent(component):
        assert component.extra_context is None

    assert component.extra_context == extra_context


def test_cacheable_component_parents_have_request_restored():
    component = FakeComponent(
        component_id="test_cacheable_component_parents_have_request_restored_1", component_name="hello-world"
    )
    component2 = FakeComponent(
        component_id="test_cacheable_component_parents_have_request_restored_2",
        component_name="hello-world",
        parent=component,
    )
    component3 = FakeComponent(
        component_id="test_cacheable_component_parents_have_request_restored_3",
        component_name="hello-world",
        parent=component2,
    )
    request = MagicMock()
    extra_content = "extra_content"
    for c in [component, component2, component3]:
        c.request = request
        c.extra_context = extra_content

    with CacheableComponent(component3):
        assert component.request is None
        assert component2.request is None
        assert component3.request is None
        assert component.extra_context is None
        assert component2.extra_context is None
        assert component3.extra_context is None

    assert component.request == request
    assert component2.request == request
    assert component3.request == request
    assert component.extra_context == extra_content
    assert component2.extra_context == extra_content
    assert component3.extra_context == extra_content


def test_restore_cached_component_children_have_request_set():
    component = FakeComponent(
        component_id="test_restore_cached_component_children_have_request_set_1", component_name="hello-world"
    )
    component2 = FakeComponent(
        component_id="test_restore_cached_component_children_have_request_set_2", component_name="hello-world"
    )
    component3 = FakeComponent(
        component_id="test_restore_cached_component_children_have_request_set_3", component_name="hello-world"
    )
    component4 = FakeComponent(
        component_id="test_restore_cached_component_children_have_request_set_4", component_name="hello-world"
    )
    component3.children.append(component4)
    component.children.extend([component2, component3])
    request = MagicMock()
    extra_content = "extra_content"
    for c in [component, component2, component3, component4]:
        c.request = request
        c.extra_context = extra_content

    with CacheableComponent(component):
        assert component.request is None
        assert component2.request is None
        assert component3.request is None
        assert component4.request is None
        assert component.extra_context is None
        assert component2.extra_context is None
        assert component3.extra_context is None
        assert component4.extra_context is None

    assert component.request == request
    assert component2.request == request
    assert component3.request == request
    assert component4.request == request
    assert component.extra_context == extra_content
    assert component2.extra_context == extra_content
    assert component3.extra_context == extra_content
    assert component4.extra_context == extra_content


class ExampleCachingComponent(UnicornView):
    name = "World"

    def get_name(self):
        return "World"

    def __str__(self):
        return f"ECC {self.component_id} - {self.component_name}"


def test_caching_components(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
    settings.UNICORN = {**settings.UNICORN, "CACHE_ALIAS": "default"}
    root = ExampleCachingComponent(component_id="test_caching_components_1", component_name="root")
    child1 = ExampleCachingComponent(
        component_id="test_caching_components_child_1", component_name="child1", parent=root
    )
    child2 = ExampleCachingComponent(
        component_id="test_caching_components_child_2", component_name="child2", parent=root
    )
    child3 = ExampleCachingComponent(
        component_id="test_caching_components_child_3", component_name="child3", parent=root
    )
    grandchild = ExampleCachingComponent(
        component_id="test_caching_components_grandchild_1", component_name="grandchild", parent=child1
    )
    grandchild2 = ExampleCachingComponent(
        component_id="test_caching_components_grandchild_2", component_name="grandchild2", parent=child1
    )
    grandchild3 = ExampleCachingComponent(
        component_id="test_caching_components_grandchild_3", component_name="grandchild3", parent=child3
    )

    cache_full_tree(child3)
    request = MagicMock()

    restored: UnicornView = restore_from_cache(child2.component_cache_key, request)

    restored_root = restored
    while restored_root.parent:
        restored_root = restored_root.parent

    assert root.component_id == restored_root.component_id
    assert 3 == len(restored_root.children)

    for i, child in enumerate([child1, child2, child3]):
        assert restored_root.children[i].component_id == child.component_id

    assert 2 == len(restored_root.children[0].children)

    for i, child in enumerate([grandchild, grandchild2]):
        assert restored_root.children[0].children[i].component_id == child.component_id

    assert not restored_root.children[1].children
    assert 1 == len(restored_root.children[2].children)
    assert grandchild3.component_id == restored_root.children[2].children[0].component_id


@patch("django_unicorn.cacher.create_template")
def test_caching_components_with_template_html(create_template):
    component = FakeComponentWithTemplateHtml(
        component_id="test_caching_components_with_template_html", component_name="template-html-test"
    )
    assert component.template_html

    # manually set template_name to None which happens outside of this code normally
    component.template_name = None

    # Caching will pop the `Template` instance from component.template_name when it enters,
    # and re-create it when it exits
    cache_full_tree(component)

    assert component.template_html
    assert isinstance(component.template_html, str)

    # check that template_name will re-create a Template based on `template_html`
    create_template.assert_called_once_with(component.template_html)


class UnpicklableObject:
    """Object that cannot be pickled, used to test pickle failure handling."""

    def __reduce__(self):
        raise TypeError("Cannot pickle this object")


class ComponentWithUnpicklableAttribute(UnicornView):
    """Component that has an attribute that cannot be pickled."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unpicklable = UnpicklableObject()


def test_cacheable_component_restores_state_on_pickle_failure():
    """Test that parent/children are restored when pickle fails.

    This is a regression test for a bug where pickle failure in CacheableComponent
    would leave parent/children as PointerUnicornView objects instead of restoring
    them to the original components.
    """

    parent = FakeComponent(
        component_id="test_pickle_failure_parent",
        component_name="parent",
    )
    child = ComponentWithUnpicklableAttribute(
        component_id="test_pickle_failure_child",
        component_name="child",
        parent=parent,
    )

    # Verify initial state
    assert child.parent is parent
    assert parent in [child.parent]
    assert child in parent.children

    # CacheableComponent should raise UnicornCacheError due to unpicklable attribute
    with pytest.raises(UnicornCacheError):
        with CacheableComponent(child):
            pass

    # After pickle failure, parent/children should be restored to original components,
    # NOT left as PointerUnicornView objects
    assert child.parent is parent, "child.parent should be restored to original parent component"
    assert not isinstance(child.parent, PointerUnicornView), "child.parent should not be PointerUnicornView"
    assert child in parent.children, "child should still be in parent.children"
    assert not any(isinstance(c, PointerUnicornView) for c in parent.children), (
        "parent.children should not contain PointerUnicornView objects"
    )


def test_cacheable_component_restores_nested_state_on_pickle_failure():
    """Test that deeply nested parent/children are all restored when pickle fails."""

    grandparent = FakeComponent(
        component_id="test_nested_pickle_failure_grandparent",
        component_name="grandparent",
    )
    parent = FakeComponent(
        component_id="test_nested_pickle_failure_parent",
        component_name="parent",
        parent=grandparent,
    )
    child = ComponentWithUnpicklableAttribute(
        component_id="test_nested_pickle_failure_child",
        component_name="child",
        parent=parent,
    )

    with pytest.raises(UnicornCacheError):
        with CacheableComponent(child):
            pass

    # All parent/children relationships should be restored
    assert child.parent is parent
    assert parent.parent is grandparent
    assert not isinstance(child.parent, PointerUnicornView)
    assert not isinstance(parent.parent, PointerUnicornView)
    assert child in parent.children
    assert parent in grandparent.children


class SimpleForm(forms.Form):
    name = forms.CharField()


class ComponentWithForm(UnicornView):
    """Component whose instance attributes include a Django Form."""

    def __init__(self, *args, **kwargs):
        self.form = kwargs.pop("form", None)
        super().__init__(*args, **kwargs)


def test_cacheable_component_strips_form_before_pickling():
    """Form instances are stripped before pickling so the component can be cached."""
    form_instance = SimpleForm()
    component = ComponentWithForm(
        component_id="test_form_strip",
        component_name="with-form",
        form=form_instance,
    )
    assert component.form is form_instance

    with CacheableComponent(component):
        # Inside context: form should be stripped (set to None) so pickle can succeed
        assert component.form is None

    # After context: form should be restored
    assert component.form is form_instance


def test_cacheable_component_restores_form_after_context():
    """Form instances are fully restored on CacheableComponent.__exit__."""
    form_instance = SimpleForm(data={"name": "Alice"})
    component = ComponentWithForm(
        component_id="test_form_restore",
        component_name="with-form",
        form=form_instance,
    )

    with CacheableComponent(component):
        pass

    assert component.form is form_instance
