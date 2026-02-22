from django_unicorn.components import UnicornView
from django_unicorn.views.action_parsers.utils import set_property_value
from django_unicorn.views.request import ComponentRequest


def handle(component_request: ComponentRequest, component: UnicornView, payload: dict):
    property_name = payload.get("name")
    property_value = payload.get("value")

    # When a file input changes, JS sends JSON.stringify(FileList) which becomes {}.
    # Resolve the actual uploaded file(s) from request.FILES instead.
    if isinstance(property_value, dict) and not property_value and property_name:
        request = component_request.request
        if request is not None and request.FILES:
            if property_name in request.FILES:
                property_value = request.FILES[property_name]
            elif f"{property_name}[0]" in request.FILES:
                # Multiple files appended as name[0], name[1], …
                files = []
                i = 0
                while f"{property_name}[{i}]" in request.FILES:
                    files.append(request.FILES[f"{property_name}[{i}]"])
                    i += 1
                property_value = files[0] if len(files) == 1 else files

    call_resolved_method = True

    # If there is more than one action then only call the resolved methods for the last action in the queue
    if len(component_request.action_queue) > 1:
        call_resolved_method = False
        last_action = component_request.action_queue[-1:][0]

        if last_action.payload.get("name") == property_name and last_action.payload.get("value") == property_value:
            call_resolved_method = True

    set_property_value(
        component, property_name, property_value, component_request.data, call_resolved_method=call_resolved_method
    )
