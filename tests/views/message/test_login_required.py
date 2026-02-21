"""
Tests for LoginRequiredMiddleware compatibility.

When `django.contrib.auth.middleware.LoginRequiredMiddleware` is present in
MIDDLEWARE, the per-component `login_not_required` attribute controls whether
unauthenticated users can trigger actions.  When the middleware is absent the
check is skipped entirely so existing projects are not affected.
"""

import time

import pytest
import shortuuid
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from django_unicorn.components import UnicornView
from django_unicorn.errors import UnicornAuthenticationError
from django_unicorn.utils import generate_checksum
from django_unicorn.views.message import UnicornMessageHandler
from django_unicorn.views.request import ComponentRequest

LOGIN_REQUIRED_MIDDLEWARE = "django.contrib.auth.middleware.LoginRequiredMiddleware"

# ── Fake components ───────────────────────────────────────────────────────────


class FakePublicComponent(UnicornView):
    """Opts into public access — reachable without authentication."""

    template_name = "templates/test_component.html"
    login_not_required = True
    count = 0

    def increment(self):
        self.count += 1


class FakeProtectedComponent(UnicornView):
    """Default behaviour — blocked when LoginRequiredMiddleware is active and
    the user is not authenticated."""

    template_name = "templates/test_component.html"
    count = 0

    def increment(self):
        self.count += 1


# ── Helper ────────────────────────────────────────────────────────────────────


def _build_handler(component_name: str, user) -> tuple:
    """
    Return *(handler, component_request)* for the given component and user.

    Uses RequestFactory so the actual middleware stack is not invoked —
    this lets us isolate just the per-component auth guard inside
    `UnicornMessageHandler._process_request`.
    """
    rf = RequestFactory()
    data: dict = {}
    payload = {
        "actionQueue": [],
        "data": data,
        "checksum": generate_checksum(data),
        "id": shortuuid.uuid()[:8],
        "epoch": time.time(),
        "hash": None,
    }
    request = rf.post(
        f"/message/{component_name}",
        data=payload,
        content_type="application/json",
    )
    request.user = user
    component_request = ComponentRequest(request, component_name)
    handler = UnicornMessageHandler(request)
    return handler, component_request


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_no_middleware_anonymous_user_passes_protected_component(settings):
    """Without LoginRequiredMiddleware in MIDDLEWARE the auth guard is never
    evaluated, so anonymous users are not blocked."""
    assert LOGIN_REQUIRED_MIDDLEWARE not in settings.MIDDLEWARE

    handler, component_request = _build_handler(
        "tests.views.message.test_login_required.FakeProtectedComponent",
        AnonymousUser(),
    )

    try:
        handler._process_request(component_request)
    except UnicornAuthenticationError:
        pytest.fail("UnicornAuthenticationError was raised even though LoginRequiredMiddleware is not configured")


def test_middleware_blocks_anonymous_on_protected_component(settings):
    """An unauthenticated user hitting a component that has not set
    `login_not_required = True` should receive UnicornAuthenticationError."""
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, LOGIN_REQUIRED_MIDDLEWARE]

    handler, component_request = _build_handler(
        "tests.views.message.test_login_required.FakeProtectedComponent",
        AnonymousUser(),
    )

    with pytest.raises(UnicornAuthenticationError):
        handler._process_request(component_request)


def test_middleware_allows_anonymous_on_public_component(settings):
    """Components that set `login_not_required = True` remain accessible to
    unauthenticated users even when LoginRequiredMiddleware is active."""
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, LOGIN_REQUIRED_MIDDLEWARE]

    handler, component_request = _build_handler(
        "tests.views.message.test_login_required.FakePublicComponent",
        AnonymousUser(),
    )

    try:
        handler._process_request(component_request)
    except UnicornAuthenticationError:
        pytest.fail("UnicornAuthenticationError was raised for a component marked login_not_required=True")


def test_middleware_allows_authenticated_user_on_protected_component(settings, django_user_model):
    """An authenticated user can always interact with any component regardless
    of the `login_not_required` flag."""
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, LOGIN_REQUIRED_MIDDLEWARE]

    user = django_user_model.objects.create_user(username="lr_test_user", password="pass")

    handler, component_request = _build_handler(
        "tests.views.message.test_login_required.FakeProtectedComponent",
        user,
    )

    try:
        handler._process_request(component_request)
    except UnicornAuthenticationError:
        pytest.fail("UnicornAuthenticationError was raised for an authenticated user")


def test_handle_returns_401_json_for_unauthenticated_protected_component(client, settings):
    """The HTTP response for a blocked unauthenticated request is 401 JSON."""
    settings.MIDDLEWARE = [
        *settings.MIDDLEWARE,
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        LOGIN_REQUIRED_MIDDLEWARE,
    ]

    from tests.views.message.utils import post_and_get_response

    response = post_and_get_response(
        client,
        url="/message/tests.views.message.test_login_required.FakeProtectedComponent",
        data={},
        return_response=True,
    )

    assert response.status_code == 401
    assert "error" in response.json()


def test_message_view_has_login_not_required_attribute():
    """On Django 5.1+, the message endpoint carries `login_required=False` (set
    by Django's `login_not_required` decorator) so LoginRequiredMiddleware lets
    the AJAX call through to the view without redirecting."""
    import django

    from django_unicorn.views import message

    if django.VERSION >= (5, 1):
        # Django's login_not_required decorator sets login_required=False
        assert getattr(message, "login_required", True) is False
