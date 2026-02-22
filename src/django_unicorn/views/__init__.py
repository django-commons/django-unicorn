import logging
from functools import wraps

try:
    # Django 5.1+ — exempts the message endpoint from LoginRequiredMiddleware
    # so AJAX calls from public pages reach it. Per-component access control
    # is enforced in UnicornMessageHandler via `Meta.login_not_required`.
    from django.contrib.auth.decorators import login_not_required
except ImportError:
    # Django < 5.1 — LoginRequiredMiddleware does not exist, nothing to do.
    def login_not_required(func):  # type: ignore[misc]
        return func


from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponseNotModified
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from django_unicorn.decorators import timed
from django_unicorn.errors import RenderNotModifiedError, UnicornAuthenticationError, UnicornViewError
from django_unicorn.views.message import UnicornMessageHandler
from django_unicorn.views.request import ComponentRequest

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def handle_error(view_func):
    """
    Returns a JSON response with an error if necessary.
    """

    def wrapped_view(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except UnicornAuthenticationError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except UnicornViewError as e:
            return JsonResponse({"error": str(e)})
        except RenderNotModifiedError:
            return HttpResponseNotModified()
        except AssertionError as e:
            return JsonResponse({"error": str(e)})

    return wraps(view_func)(wrapped_view)


@timed
@handle_error
@ensure_csrf_cookie
@csrf_protect  # type: ignore
@require_POST  # type: ignore
@login_not_required
def message(request: HttpRequest, component_name: str | None = None) -> JsonResponse:  # type: ignore
    """
    Endpoint that instantiates the component and does the correct action
    (set an attribute or call a method) depending on the JSON payload in the body.

    Args:
        param request: HttpRequest for the function-based view.
        param: component_name: Name of the component, e.g. "hello-world".

    Returns:
        `JsonRequest` with the following structure in the body:
        {
        "id": component_id,
        "dom": html,  # re-rendered version of the component after actions in the payload are completed
        "data": {},  # updated data after actions in the payload are completed
        "errors": {},  # form validation errors
        "return": {}, # optional return value from an executed action
        "parent": {}  # optional representation of the parent component
        }
    """

    if not component_name:
        raise AssertionError("Missing component name in url")

    component_request = ComponentRequest(request, component_name)
    handler = UnicornMessageHandler(request)
    json_result = handler.handle(component_request)

    return JsonResponse(json_result, json_dumps_params={"separators": (",", ":")})
