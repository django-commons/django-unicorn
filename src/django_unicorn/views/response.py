from typing import Any

from django_unicorn.components import UnicornView
from django_unicorn.components.unicorn_template_response import get_root_element
from django_unicorn.errors import RenderNotModifiedError
from django_unicorn.serializer import loads
from django_unicorn.utils import generate_checksum, html_element_to_string
from django_unicorn.views.request import ComponentRequest


class ComponentResponse:
    __slots__ = ("component", "component_request", "partials", "return_data")

    def __init__(
        self,
        component: UnicornView,
        component_request: ComponentRequest,
        return_data: Any | None = None,
        partials: list[dict[str, Any]] | None = None,
    ):
        self.component = component
        self.component_request = component_request
        self.return_data = return_data
        self.partials = partials or []

    def _collect_all_calls(self) -> list[dict[str, Any]]:
        """
        Collect JavaScript calls from this component and all its children recursively.

        Returns:
            List of call dictionaries with 'fn' and 'args' keys.
        """
        all_calls = list(self.component.calls)  # Start with parent's calls

        # Recursively collect from all children
        all_calls.extend(self._collect_calls_from_component(self.component))

        return all_calls

    def _collect_calls_from_component(self, component: UnicornView) -> list[dict[str, Any]]:
        """
        Helper to recursively collect calls from a component's descendants.

        Args:
            component: The component to collect calls from.

        Returns:
            List of call dictionaries from all descendants.
        """
        calls = []
        for child in component.children:
            # Add this child's calls
            calls.extend(child.calls)
            # Recursively collect from this child's descendants
            calls.extend(self._collect_calls_from_component(child))
        return calls

    def get_data(self) -> dict[str, Any]:
        # Sort data so it's stable
        if self.component_request.data:
            self.component_request.data = {
                key: self.component_request.data[key] for key in sorted(self.component_request.data)
            }

        result = {
            "id": self.component_request.id,
            "data": self.component_request.data,
            "errors": self.component.errors,
            "calls": self._collect_all_calls(),
            "checksum": generate_checksum(self.component_request.data),
            "epoch": self.component_request.epoch,
        }

        render_not_modified = False
        root_element = None
        rendered_component = self.component.last_rendered_dom  # type: ignore

        if self.partials:
            result.update({"partials": self.partials})
        else:
            rendered_component_hash = generate_checksum(rendered_component)

            if (
                self.component_request.hash == rendered_component_hash
                and (not self.return_data or not self.return_data.value)
                and not self._collect_all_calls()
            ):
                if not self.component.parent and self.component.force_render is False:
                    raise RenderNotModifiedError()
                else:
                    render_not_modified = True

            root_element = get_root_element(rendered_component)
            rendered_component = html_element_to_string(root_element)

            result.update(
                {
                    "dom": rendered_component,
                    "hash": rendered_component_hash,
                }
            )

        if self.return_data:
            result.update(
                {
                    "return": self.return_data.get_data(),
                }
            )

            if self.return_data.redirect:
                result.update(
                    {
                        "redirect": self.return_data.redirect,
                    }
                )

            if self.return_data.poll:
                result.update(
                    {
                        "poll": self.return_data.poll,
                    }
                )

        parent_component = self.component.parent
        parent_result = result

        while parent_component:
            if parent_component.force_render is True:
                # TODO: Should parent_component.hydrate() be called?
                parent_frontend_context_variables = loads(parent_component.get_frontend_context_variables())
                parent_checksum = generate_checksum(str(parent_frontend_context_variables))

                parent = {
                    "id": parent_component.component_id,
                    "checksum": parent_checksum,
                }

                if not self.partials:
                    # Get re-generated child checksum and update the child component inside the parent DOM
                    parent_dom = parent_component.render()
                    self.component.parent_rendered(parent_dom)

                    if root_element is None:
                        raise AssertionError("Missing root element")

                    # Use lxml for attribute extraction
                    child_checksum = root_element.get("unicorn:checksum")
                    child_unicorn_id = root_element.get("unicorn:id")

                    # Parse parent DOM
                    parent_soup = get_root_element(parent_dom)

                    # Find child in parent and update checksum
                    if parent_soup.get("unicorn:id") == child_unicorn_id:
                        parent_soup.set("unicorn:checksum", child_checksum)
                    else:
                        # lxml iter is recursive, so this finds nested components too.
                        for _child in parent_soup.iter():
                            if child_unicorn_id == _child.get("unicorn:id"):
                                _child.set("unicorn:checksum", child_checksum)

                    parent_dom = html_element_to_string(parent_soup)

                    # Remove the child DOM from the payload since the parent DOM supersedes it
                    result["dom"] = None

                    parent.update(
                        {
                            "dom": parent_dom,
                            "data": parent_frontend_context_variables,
                            "errors": parent_component.errors,
                            "hash": generate_checksum(parent_dom),
                        }
                    )

                if render_not_modified:
                    # TODO: Determine if all parents have not changed and return a 304 if
                    # that's the case
                    pass

                parent_result.update({"parent": parent})
                parent_result = parent

            self.component = parent_component
            parent_component = parent_component.parent

        return result
