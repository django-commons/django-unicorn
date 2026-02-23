import logging
import pickle
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django_unicorn.components.unicorn_view import UnicornView

from django.core.cache import caches
from django.forms import BaseForm
from django.http import HttpRequest

from django_unicorn.errors import UnicornCacheError
from django_unicorn.settings import get_cache_alias
from django_unicorn.utils import create_template

logger = logging.getLogger(__name__)


class PointerUnicornView:
    """Lightweight placeholder for UnicornView during caching.

    This class is used to break circular references when pickling components.
    It should ONLY be used during cache serialization/deserialization.
    If this class is accessed outside of caching context, it indicates a bug.
    """

    def __init__(self, component_cache_key):
        self.component_cache_key = component_cache_key
        self.parent = None
        self.children = []


class CacheableComponent:
    """
    Updates a component into something that is cacheable/pickleable. Also set pointers to parents/children.
    Use in a `with` statement or explicitly call `__enter__` `__exit__` to use. It will restore the original component
    on exit.
    """

    def __init__(self, component: "UnicornView"):
        self._state: dict = {}
        self.cacheable_component = component

    def __enter__(self):
        components = []
        components.append(self.cacheable_component)

        while components:
            component = components.pop()

            if component.component_id in self._state:
                continue

            if hasattr(component, "extra_context"):
                extra_context = component.extra_context
                component.extra_context = None
            else:
                extra_context = None

            # Pop the request off for pickling
            request = component.request
            component.request = None

            template_name = component.template_name

            # Pop the template_name off for pickling, but only if it's not a string, aka it's a `Template`
            if not isinstance(component.template_name, str):
                component.template_name = None

            # Strip Django Form instances before pickling — forms contain unpicklable
            # references (e.g. lazily-bound validators) and are only needed for rendering.
            form_attributes: dict = {}
            for attr_name, attr_val in list(vars(component).items()):
                if isinstance(attr_val, BaseForm):
                    form_attributes[attr_name] = attr_val
                    setattr(component, attr_name, None)

            self._state[component.component_id] = (
                component,
                request,
                extra_context,
                component.parent,
                component.children.copy(),
                template_name,
                form_attributes,
            )

            if component.parent:
                components.append(component.parent)
                component.parent = PointerUnicornView(component.parent.component_cache_key)

            for index, child in enumerate(component.children):
                components.append(child)
                component.children[index] = PointerUnicornView(child.component_cache_key)

        # Verify all components can be pickled. If any fail, we MUST restore state
        # before raising the exception, otherwise parent/children will be left as
        # PointerUnicornView objects.
        try:
            for component, *_ in self._state.values():
                pickle.dumps(component)
        except (
            TypeError,
            AttributeError,
            NotImplementedError,
            pickle.PicklingError,
        ) as e:
            # Restore state before raising!
            self.__exit__(None, None, None)
            raise UnicornCacheError(
                f"Cannot cache component '{type(component)}' because it is not picklable: {type(e)}: {e}"
            ) from e

        return self

    def __exit__(self, *args):
        for component, request, extra_context, parent, children, template_name, form_attributes in self._state.values():
            component.request = request
            component.parent = parent
            component.children = children
            component.template_name = template_name

            # Restore any form instances that were stripped before pickling
            for attr_name, attr_val in form_attributes.items():
                setattr(component, attr_name, attr_val)

            # Re-create the template_name `Template` object if it is `None`
            if component.template_name is None and hasattr(component, "template_html"):
                component.template_name = create_template(component.template_html)

            if extra_context:
                component.extra_context = extra_context

    def components(self) -> list["UnicornView"]:
        return [component for component, *_ in self._state.values()]


def cache_full_tree(component: "UnicornView"):
    root = component

    while root.parent:
        root = root.parent

    cache = caches[get_cache_alias()]

    with CacheableComponent(root) as caching:
        for _component in caching.components():
            cache.set(_component.component_cache_key, _component)


def restore_from_cache(component_cache_key: str, request: HttpRequest | None = None) -> "UnicornView":
    """
    Gets a cached unicorn view by key, restoring and getting cached parents and children
    and setting the request.
    """

    cache = caches[get_cache_alias()]
    cached_component = cache.get(component_cache_key)

    if cached_component:
        roots = {}
        root: UnicornView = cached_component
        roots[root.component_cache_key] = root

        while root.parent:
            root = cache.get(root.parent.component_cache_key)
            roots[root.component_cache_key] = root

        to_traverse: list[UnicornView] = []
        to_traverse.append(root)

        while to_traverse:
            current = to_traverse.pop()
            if request:
                current.setup(request)
            current._validate_called = False
            current.calls = []

            for index, child in enumerate(current.children):
                key = child.component_cache_key
                cached_child = roots.pop(key, None) or cache.get(key)

                cached_child.parent = current
                current.children[index] = cached_child
                to_traverse.append(cached_child)

    return cached_component
