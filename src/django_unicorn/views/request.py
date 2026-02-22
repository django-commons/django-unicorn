import logging

from django_unicorn.call_method_parser import parse_call_method_name
from django_unicorn.errors import UnicornViewError
from django_unicorn.serializer import JSONDecodeError, loads
from django_unicorn.utils import generate_checksum
from django_unicorn.views.action import Action, CallMethod, Refresh, Reset, SyncInput, Toggle

logger = logging.getLogger(__name__)


class ComponentRequest:
    """
    Parses, validates, and stores all of the data from the message request.
    """

    __slots__ = (
        "action_queue",
        "body",
        "data",
        "epoch",
        "hash",
        "id",
        "key",
        "name",
        "request",
    )

    def __init__(self, request, component_name):
        self.body = {}
        self.request = request

        try:
            self.body = loads(request.body)

            if not self.body:
                raise AssertionError("Invalid JSON body")
        except JSONDecodeError as e:
            raise UnicornViewError("Body could not be parsed") from e

        self.name = component_name
        if not self.name:
            raise AssertionError("Missing component name")

        self.data = self.body.get("data")
        if self.data is None:
            raise AssertionError("Missing data")

        self.id = self.body.get("id")
        if not self.id:
            raise AssertionError("Missing component id")

        self.epoch = self.body.get("epoch", "")
        self.key = self.body.get("key", "")
        self.hash = self.body.get("hash", "")
        meta = self.body.get("meta", "")

        if meta and ":" in meta:
            parts = meta.split(":")
            meta = parts[0]

            if len(parts) > 1:
                self.hash = parts[1]

            if len(parts) > 2:  # noqa: PLR2004
                self.epoch = parts[2]

        if not self.epoch:
            raise AssertionError("Missing epoch")

        self.validate_checksum(meta)

        self.action_queue = []

        for action_data in self.body.get("actionQueue", []):
            action_type = action_data.get("type")
            payload = action_data.get("payload", {})

            if action_type == "syncInput":
                self.action_queue.append(SyncInput(action_data))
            elif action_type == "callMethod":
                name = payload.get("name", "")
                method_name, _, _ = parse_call_method_name(name)

                if method_name == "$refresh":
                    self.action_queue.append(Refresh(action_data))
                elif method_name == "$reset":
                    self.action_queue.append(Reset(action_data))
                elif method_name == "$toggle":
                    self.action_queue.append(Toggle(action_data))
                else:
                    self.action_queue.append(CallMethod(action_data))
            else:
                self.action_queue.append(Action(action_data))

    def __repr__(self):
        return (
            f"ComponentRequest(name='{self.name}' id='{self.id}' key='{self.key}'"
            f" epoch={self.epoch} data={self.data} action_queue={self.action_queue} hash={self.hash})"
        )

    def validate_checksum(self, meta: str | None = None):
        """
        Validates that the checksum in the request matches the data.

        Returns:
            Raises `AssertionError` if the checksums don't match.
        """
        if not meta:
            meta = self.body.get("meta")

        if not meta:
            raise AssertionError("Missing meta")

        generated_checksum = generate_checksum(self.data)

        if meta != generated_checksum:
            raise AssertionError("Checksum does not match")
