import copy
import logging

import orjson
from django.core.cache import caches
from django.forms import ValidationError
from django.http import HttpRequest

from django_unicorn.cacher import cache_full_tree
from django_unicorn.components import UnicornView
from django_unicorn.components.unicorn_template_response import get_root_element
from django_unicorn.errors import RenderNotModifiedError, UnicornViewError
from django_unicorn.settings import get_cache_alias, get_serial_enabled, get_serial_timeout
from django_unicorn.utils import html_element_to_string
from django_unicorn.views.action import Action, CallMethod, Refresh, Reset, SyncInput, Toggle
from django_unicorn.views.action_parsers import call_method, sync_input
from django_unicorn.views.request import ComponentRequest
from django_unicorn.views.response import ComponentResponse
from django_unicorn.views.utils import set_property_from_data

logger = logging.getLogger(__name__)

MIN_VALIDATION_ERROR_ARGS = 2


class UnicornMessageHandler:
    def __init__(self, request: HttpRequest):
        self.request = request

    def handle(self, component_request: ComponentRequest) -> dict:
        """
        Process a `ComponentRequest` by adding it to the cache and then either:
            - processing all of the component requests in the cache and returning the resulting value if
                it is the first component request for that particular component name + component id combination
            - return a `dict` saying that the request has been queued
        """
        if not get_serial_enabled():
            return self._process_request(component_request)

        cache = caches[get_cache_alias()]
        queue_cache_key = f"unicorn:queue:{component_request.id}"
        component_requests = cache.get(queue_cache_key) or []

        # Remove `request` from `ComponentRequest` before caching because it is not pickleable
        component_request.request = None
        component_requests.append(component_request)

        cache.set(
            queue_cache_key,
            component_requests,
            timeout=get_serial_timeout(),
        )

        if len(component_requests) > 1:
            original_epoch = component_requests[0].epoch
            return {
                "queued": True,
                "epoch": component_request.epoch,
                "original_epoch": original_epoch,
            }

        return self._handle_queued_component_requests(queue_cache_key)

    def _handle_queued_component_requests(self, queue_cache_key) -> dict:
        cache = caches[get_cache_alias()]
        component_requests = cache.get(queue_cache_key)

        if not component_requests or not isinstance(component_requests, list):
            raise UnicornViewError(f"No request found for {queue_cache_key}")

        component_requests = sorted(component_requests, key=lambda r: r.epoch)
        first_component_request = component_requests[0]

        # Restore request object since it was removed for pickling
        first_component_request.request = self.request

        try:
            first_json_result = self._process_request(first_component_request)
        except RenderNotModifiedError:
            raise
        finally:
            component_requests = cache.get(queue_cache_key)
            if component_requests:
                component_requests.pop(0)
                cache.set(
                    queue_cache_key,
                    component_requests,
                    timeout=get_serial_timeout(),
                )

        if component_requests:
            merged_component_request = None
            for additional_component_request in copy.deepcopy(component_requests):
                if merged_component_request:
                    merged_component_request.action_queue.extend(additional_component_request.action_queue)
                else:
                    merged_component_request = additional_component_request
                    for key, val in first_json_result.get("data", {}).items():
                        merged_component_request.data[key] = val

                component_requests.pop(0)
                cache.set(
                    queue_cache_key,
                    component_requests,
                    timeout=get_serial_timeout(),
                )

            if merged_component_request:
                merged_component_request.request = self.request
                return self.handle(merged_component_request)

        return first_json_result

    def _process_request(self, component_request: ComponentRequest) -> dict:
        component = UnicornView.create(
            component_id=component_request.id,
            component_name=component_request.name,
            request=self.request,
        )

        # Make sure that there is always a request on the component if needed
        if component.request is None:
            component.request = self.request

        if component.parent is not None and component.parent.request is None:
            component.parent.request = self.request

        if component_request.data is None:
            raise AssertionError("Component request data is required")
        original_data = copy.deepcopy(component_request.data)

        component.pre_parse()

        for property_name, property_value in component_request.data.items():
            set_property_from_data(component, property_name, property_value, ignore_m2m=True)

        component.post_parse()

        component.hydrate()

        validate_all_fields = False
        is_reset_called = False
        is_refresh_called = False
        return_data = None
        partials = []

        for action in component_request.action_queue:
            if action.partials:
                partials.extend(action.partials)

            # TODO: Refactor this to use polymorphism on Action classes if possible
            # For now, map back to existing handlers logic

            if isinstance(action, SyncInput):
                # Reconstruct payload for existing handler
                # existing handler expects {"name": ..., "value": ...}
                sync_input.handle(component_request, component, action.payload)
            elif isinstance(action, CallMethod | Refresh | Reset | Toggle):
                # Refresh and Reset are handled inside call_method.handle currently via special methods
                # or we might need to handle them explicitly if we changed something.
                # Since I'm using the existing call_method.handle, and it parses "name",
                # I should pass the payload which contains the "name" (e.g. "$refresh" or "method()").
                # My `views/request.py` parses these into classes but action.payload is still the original dict.

                try:
                    (
                        component,
                        _is_refresh_called,
                        _is_reset_called,
                        _validate_all_fields,
                        return_data,
                    ) = call_method.handle(component_request, component, action.payload)

                    is_refresh_called = is_refresh_called | _is_refresh_called
                    is_reset_called = is_reset_called | _is_reset_called
                    validate_all_fields = validate_all_fields | _validate_all_fields
                except ValidationError as e:
                    component._handle_validation_error(e)
            elif isinstance(action, Action):
                # Fallback/Generic?
                if action.action_type == "syncInput":
                    sync_input.handle(component_request, component, action.payload)
                elif action.action_type == "callMethod":
                    # ...
                    pass
                else:
                    logger.warning(f"Unknown action_type '{action.action_type}'")

        component.complete()

        # Re-load frontend context variables
        component_request.data = orjson.loads(component.get_frontend_context_variables())

        # Safe fields handling
        component._handle_safe_fields()

        # Updated data calculation
        updated_data = component_request.data
        if not is_reset_called:
            if not is_refresh_called:
                updated_data = {}
                for key, value in original_data.items():
                    if value != component_request.data.get(key):
                        updated_data[key] = component_request.data.get(key)

            if validate_all_fields:
                component.validate()
            else:
                component.validate(model_names=list(updated_data.keys()))

        # Queued messages handling
        self._handle_queued_messages(component, return_data)

        # Persist any child component state changes to cache before rendering.
        # Without this, template tags that re-create child components from cache
        # would retrieve stale state, ignoring changes made by the parent method.
        cache_full_tree(component)

        # Render
        rendered_component = component.render(request=self.request, epoch=component_request.epoch)
        component.rendered(rendered_component)

        # Restore queued messages
        self._restore_queued_messages(component)

        partial_doms = []
        if partials:
            soup = get_root_element(rendered_component)

            for partial in partials:
                target = partial.get("target") or partial.get("key") or partial.get("id")
                if not target:
                    raise AssertionError("Partial target is required")

                found = False

                # Check root element
                if soup.get("unicorn:key") == target:
                    partial_doms.append({"key": target, "dom": html_element_to_string(soup, with_tail=False)})
                    found = True
                    continue

                if soup.get("id") == target:
                    partial_doms.append({"id": target, "dom": html_element_to_string(soup, with_tail=False)})
                    found = True
                    continue

                # Check children
                for element in soup.iter():
                    if element.get("unicorn:key") == target:
                        partial_doms.append({"key": target, "dom": html_element_to_string(element, with_tail=False)})
                        found = True
                        break

                if not found:
                    for element in soup.iter():
                        if element.get("id") == target:
                            partial_doms.append({"id": target, "dom": html_element_to_string(element, with_tail=False)})
                            found = True
                            break

        # Store last rendered dom for ComponentResponse to use
        component.last_rendered_dom = rendered_component

        response = ComponentResponse(component, component_request, return_data=return_data, partials=partial_doms)
        return response.get_data()

    def _handle_queued_messages(self, component, return_data):
        self.request_queued_messages = []
        if return_data and return_data.redirect and "url" in return_data.redirect:
            try:
                self.request_queued_messages = copy.deepcopy(component.request._messages._queued_messages)
                component.request._messages._queued_messages = []
            except AttributeError as e:
                logger.warning(e)

    def _restore_queued_messages(self, component):
        if hasattr(self, "request_queued_messages") and self.request_queued_messages:
            try:
                component.request._messages._queued_messages = self.request_queued_messages
            except AttributeError as e:
                logger.warning(e)
