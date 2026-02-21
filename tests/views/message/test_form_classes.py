"""
Integration tests for the ``form_classes`` validation feature (issue #220).

These tests post ``syncInput`` and ``callMethod`` actions against
``FakeFormClassesComponent`` and verify that validation errors for dotted paths
(e.g. ``book.title``) are correctly surfaced in the response JSON.
"""

import pytest
from tests.views.message.utils import post_and_get_response


COMPONENT_URL = "/message/tests.views.fake_components.FakeFormClassesComponent"


def _post(client, data, action_queue):
    return post_and_get_response(
        client,
        url=COMPONENT_URL,
        data=data,
        action_queue=action_queue,
    )


# ── syncInput actions ──────────────────────────────────────────────────────────


def test_sync_input_book_title_empty_triggers_error(client):
    """
    When ``book.title`` is synced with an empty string the response should
    contain a ``required`` validation error at ``book.title``.
    """
    data = {"book": {"title": "", "date_published": ""}}
    body = _post(
        client,
        data=data,
        action_queue=[
            {
                "type": "syncInput",
                "payload": {"name": "book.title", "value": ""},
                "partials": [],
            }
        ],
    )

    assert body["errors"], f"Expected errors, got: {body['errors']}"
    assert "book.title" in body["errors"], f"book.title not in errors: {body['errors']}"
    assert body["errors"]["book.title"][0]["code"] == "required"


def test_sync_input_book_title_valid_no_error(client):
    """
    When ``book.title`` is synced with a valid non-empty string the response
    should NOT contain a validation error at ``book.title``.
    (``book.date_published`` may still have an error; we don't check that here.)
    """
    data = {"book": {"title": "My Book", "date_published": ""}}
    body = _post(
        client,
        data=data,
        action_queue=[
            {
                "type": "syncInput",
                "payload": {"name": "book.title", "value": "My Book"},
                "partials": [],
            }
        ],
    )

    assert "book.title" not in body.get("errors", {})


# ── callMethod (save) actions ──────────────────────────────────────────────────


def test_call_save_with_empty_book_returns_errors(client):
    """
    Calling the ``save`` method on a component with an empty book object should
    trigger validation and return errors for all required fields.
    """
    data = {"book": {"title": "", "date_published": ""}}
    body = _post(
        client,
        data=data,
        action_queue=[
            {
                "type": "callMethod",
                "payload": {"name": "save"},
            }
        ],
    )

    assert body["errors"], f"Expected errors from save(), got: {body['errors']}"
    assert "book.title" in body["errors"]
    assert body["errors"]["book.title"][0]["code"] == "required"
    assert "book.date_published" in body["errors"]


def test_call_save_with_valid_book_no_errors(client):
    """
    Calling ``save`` when book has all required fields should produce no errors.
    """
    data = {"book": {"title": "Clean Title", "date_published": "2024-01-01"}}
    body = _post(
        client,
        data=data,
        action_queue=[
            {
                "type": "callMethod",
                "payload": {"name": "save"},
            }
        ],
    )

    assert not body.get("errors"), f"Expected no errors, got: {body.get('errors')}"
