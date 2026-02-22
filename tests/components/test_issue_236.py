"""
Regression test for issue #236: self.request is None in child components.

https://github.com/django-commons/django-unicorn/discussions/236

Both self.request and self.parent.request must be the live HttpRequest object
(not None and not a bare HttpRequest()) when accessed inside mount() of a child
component.
"""

import shortuuid
from django.test import RequestFactory

from django_unicorn.components import UnicornView


class ParentView236(UnicornView):
    template_name = "templates/test_component.html"


class ChildView236(UnicornView):
    """Captures self.request and self.parent.request inside mount()."""

    template_name = "templates/test_component.html"

    # These are populated during mount(); None means mount() didn't set them.
    request_in_mount: object = None
    parent_request_in_mount: object = None

    def mount(self):
        self.request_in_mount = self.request
        if self.parent is not None:
            self.parent_request_in_mount = self.parent.request


PARENT_NAME = "tests.components.test_issue_236.ParentView236"
CHILD_NAME = "tests.components.test_issue_236.ChildView236"


def test_issue_236_child_request_set_in_mount():
    """
    self.request must be the real HttpRequest inside a child component's mount().
    Previously self.request was None (or a bare HttpRequest()) so user-specific
    data (e.g. request.user) was not accessible.
    """
    request = RequestFactory().get("/")

    parent_id = shortuuid.uuid()[:8]
    child_id = f"{parent_id}:{CHILD_NAME}"

    parent = UnicornView.create(
        component_id=parent_id,
        component_name=PARENT_NAME,
        request=request,
    )

    child = UnicornView.create(
        component_id=child_id,
        component_name=CHILD_NAME,
        parent=parent,
        request=request,
    )

    # self.request must be the actual HttpRequest, not None or a bare HttpRequest()
    assert child.request is request, (
        "child.request should be the live HttpRequest; was None or a bare HttpRequest() before issue #236 was fixed."
    )

    # The value captured *during* mount() must also be the real request
    assert child.request_in_mount is request, (
        "self.request inside child.mount() should be the live HttpRequest, not None."
    )


def test_issue_236_parent_request_accessible_from_child():
    """
    self.parent.request must also be the real HttpRequest inside a child component.
    Previously self.parent.request was None so the child could not read the
    parent's request (e.g. to get the authenticated user).
    """
    request = RequestFactory().get("/")

    parent_id = shortuuid.uuid()[:8]
    child_id = f"{parent_id}:{CHILD_NAME}"

    parent = UnicornView.create(
        component_id=parent_id,
        component_name=PARENT_NAME,
        request=request,
    )

    child = UnicornView.create(
        component_id=child_id,
        component_name=CHILD_NAME,
        parent=parent,
        request=request,
    )

    assert child.parent is parent, "Sanity-check: child.parent must be the parent object."
    assert child.parent.request is request, (
        "child.parent.request should be the live HttpRequest; was None or empty before issue #236 was fixed."
    )
    # The value captured *during* mount() must reflect the parent's request
    assert child.parent_request_in_mount is request, (
        "self.parent.request inside child.mount() should be the live HttpRequest."
    )
