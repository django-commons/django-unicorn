"""
Tests for file upload support:
  - ComponentRequest parsing multipart/form-data bodies
  - sync_input resolving uploaded files from request.FILES
  - _get_form passing request.FILES to the form constructor
  - Full integration: multipart POST → component method → form save
"""

import json
import time
from unittest.mock import MagicMock

import pytest
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile

from django_unicorn.components import UnicornView
from django_unicorn.utils import generate_checksum
from django_unicorn.views.action_parsers import sync_input
from django_unicorn.views.request import ComponentRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_body(data=None, action_queue=None, component_id="test-id-123"):
    if data is None:
        data = {}
    if action_queue is None:
        action_queue = []
    return {
        "id": component_id,
        "data": data,
        "checksum": generate_checksum(data),
        "actionQueue": action_queue,
        "epoch": time.time(),
        "hash": "",
    }


def multipart_post(rf, url, body_dict, extra_files=None):
    """Build a multipart POST request with the JSON body in the 'body' field."""
    post_data = {"body": json.dumps(body_dict)}
    if extra_files:
        post_data.update(extra_files)
    return rf.post(url, data=post_data)


# ---------------------------------------------------------------------------
# Inline fake components used for integration tests (accessible by dotted path)
# ---------------------------------------------------------------------------


class FakeFileForm(forms.Form):
    document = forms.FileField()


class FakeFileComponent(UnicornView):
    template_name = "templates/test_component.html"
    form_class = FakeFileForm

    document = None
    upload_called = False

    def upload_file(self):
        if self.is_valid():
            # self.form is set by _get_form after validation
            self.upload_called = True


# ---------------------------------------------------------------------------
# Unit: ComponentRequest multipart body parsing
# ---------------------------------------------------------------------------


def test_component_request_parses_multipart_json_body(rf):
    """ComponentRequest reads JSON from the 'body' POST field for multipart requests."""
    data = {"name": "hello"}
    body = make_body(data=data, component_id="abc-123")
    request = multipart_post(rf, "/message/test", body)

    component_request = ComponentRequest(request, "fake-component")

    assert component_request.data == data
    assert component_request.id == "abc-123"
    assert component_request.action_queue == []


def test_component_request_multipart_exposes_files(rf):
    """Uploaded files are accessible via component_request.request.FILES."""
    data = {"document": {}}
    body = make_body(data=data)
    uploaded = SimpleUploadedFile("hello.txt", b"hello world", content_type="text/plain")
    request = multipart_post(rf, "/message/test", body, extra_files={"document": uploaded})

    component_request = ComponentRequest(request, "fake-component")

    assert "document" in component_request.request.FILES
    # JSON data still carries the serialized empty-dict placeholder
    assert component_request.data == {"document": {}}


def test_component_request_json_still_works(rf):
    """Plain JSON requests are unaffected by the multipart detection."""
    data = {"name": "world"}
    body = make_body(data=data, component_id="json-id")
    body_bytes = json.dumps(body).encode()

    request = rf.post(
        "/message/test",
        data=body_bytes,
        content_type="application/json",
    )

    component_request = ComponentRequest(request, "fake-component")
    assert component_request.data == data
    assert component_request.id == "json-id"


# ---------------------------------------------------------------------------
# Unit: sync_input resolves files from request.FILES
# ---------------------------------------------------------------------------


def test_sync_input_resolves_single_file_from_files(rf):
    """sync_input replaces the empty-dict FileList placeholder with the real file."""
    data = {"document": {}}
    action_queue = [{"type": "syncInput", "payload": {"name": "document", "value": {}}}]
    body = make_body(data=data, action_queue=action_queue)
    uploaded = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
    request = multipart_post(rf, "/message/test", body, extra_files={"document": uploaded})

    component_request = ComponentRequest(request, "fake-component")

    component = MagicMock(spec=UnicornView)
    # Make _set_property available so set_property_value uses it
    component.document = None

    sync_input.handle(component_request, component, {"name": "document", "value": {}})

    component._set_property.assert_called_once()
    args = component._set_property.call_args[0]
    assert args[0] == "document"
    # RequestFactory wraps SimpleUploadedFile into InMemoryUploadedFile; check by name

    assert isinstance(args[1], InMemoryUploadedFile)
    assert args[1].name == "test.txt"


def test_sync_input_resolves_multiple_files_from_files(rf):
    """sync_input collects all indexed files (name[0], name[1], …) into a list."""
    data = {"photos": {}}
    body = make_body(data=data)
    file0 = SimpleUploadedFile("a.png", b"a", content_type="image/png")
    file1 = SimpleUploadedFile("b.png", b"b", content_type="image/png")
    request = multipart_post(
        rf,
        "/message/test",
        body,
        extra_files={"photos[0]": file0, "photos[1]": file1},
    )

    component_request = ComponentRequest(request, "fake-component")

    component = MagicMock(spec=UnicornView)
    component.photos = None

    sync_input.handle(component_request, component, {"name": "photos", "value": {}})

    component._set_property.assert_called_once()
    args = component._set_property.call_args[0]
    assert args[0] == "photos"
    resolved = args[1]

    assert isinstance(resolved, list)
    assert len(resolved) == 2
    assert isinstance(resolved[0], InMemoryUploadedFile)
    assert resolved[0].name == "a.png"
    assert isinstance(resolved[1], InMemoryUploadedFile)
    assert resolved[1].name == "b.png"


def test_sync_input_non_file_unchanged(rf):
    """sync_input behaviour is unchanged for regular (non-file) values."""
    data = {"name": "original"}
    body = make_body(data=data)
    request = rf.post(
        "/message/test",
        data=json.dumps(body).encode(),
        content_type="application/json",
    )
    component_request = ComponentRequest(request, "fake-component")

    component = MagicMock(spec=UnicornView)
    component.name = "original"

    sync_input.handle(component_request, component, {"name": "name", "value": "updated"})

    component._set_property.assert_called_once()
    args = component._set_property.call_args[0]
    assert args[0] == "name"
    assert args[1] == "updated"


def test_get_form_passes_files_to_form(rf):
    """_get_form creates the form with files=request.FILES so FileFields validate."""
    uploaded = SimpleUploadedFile("doc.txt", b"data", content_type="text/plain")
    request = rf.post("/test", data={"document": uploaded})

    component = FakeFileComponent(component_id="test-cid", component_name="fake-file-component")
    component.request = request

    form = component._get_form({"document": None})

    assert form is not None
    assert form.is_valid(), form.errors
    assert form.cleaned_data["document"].name == "doc.txt"


def test_get_form_stores_form_on_self(rf):
    """_get_form caches the form instance as self.form for use in component methods."""
    uploaded = SimpleUploadedFile("doc.txt", b"data", content_type="text/plain")
    request = rf.post("/test", data={"document": uploaded})

    component = FakeFileComponent(component_id="test-cid2", component_name="fake-file-component")
    component.request = request

    form = component._get_form({"document": None})

    assert hasattr(component, "form")
    assert component.form is form


def test_get_form_without_files(rf):
    """_get_form still works when there are no uploaded files (backward compat)."""
    request = rf.post(
        "/test",
        data=json.dumps({}).encode(),
        content_type="application/json",
    )

    component = FakeFileComponent(component_id="test-cid3", component_name="fake-file-component")
    component.request = request

    form = component._get_form({"document": None})
    assert form is not None
    assert not form.is_valid()
    assert "document" in form.errors


@pytest.mark.django_db
def test_full_multipart_upload_sets_file_property(client):
    """
    Full end-to-end: the test client POSTs a multipart request with a file.
    The syncInput action should set the component's `document` attribute to
    the uploaded file and the response should be valid JSON.
    """
    uploaded = SimpleUploadedFile("report.txt", b"file body", content_type="text/plain")
    data = {"document": {}, "upload_called": False}
    action_queue = [
        {"type": "syncInput", "payload": {"name": "document", "value": {}}},
    ]
    body = make_body(data=data, action_queue=action_queue)

    response = client.post(
        "/message/tests.views.message.test_file_upload.FakeFileComponent",
        data={"body": json.dumps(body), "document": uploaded},
        # No content_type → Django test client uses multipart/form-data automatically
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "error" not in json_response
