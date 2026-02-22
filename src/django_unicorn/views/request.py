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

        content_type = request.META.get("CONTENT_TYPE", "") or ""

        try:
            if isinstance(content_type, str) and "multipart/form-data" in content_type:
                # JS sends the full JSON payload as a 'body' field in FormData;
                body_str = request.POST.get("body", "")
                if not body_str:
                    raise UnicornViewError("Body could not be parsed")
                self.body = loads(body_str)
            else:
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
        if not self.epoch:
            raise AssertionError("Missing epoch")

        self.key = self.body.get("key", "")
        self.hash = self.body.get("hash", "")

        self.validate_checksum()

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

    def validate_checksum(self):
        """
        Validates that the checksum in the request matches the data.

        Returns:
            Raises `AssertionError` if the checksums don't match.
        """
        checksum = self.body.get("checksum")

        if not checksum:
            raise AssertionError("Missing checksum")

        generated_checksum = generate_checksum(self.data)

        if checksum != generated_checksum:
            raise AssertionError("Checksum does not match")
