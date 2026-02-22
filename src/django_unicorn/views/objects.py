import logging

from django.http.response import HttpResponseRedirect

from django_unicorn.components import HashUpdate, LocationUpdate, PollUpdate
from django_unicorn.errors import UnicornViewError
from django_unicorn.serializer import JSONDecodeError, dumps, loads
from django_unicorn.utils import generate_checksum, is_int

logger = logging.getLogger(__name__)


class Action:
    """
    Action that gets queued.
    """

    def __init__(self, data):
        self.action_type = data.get("type")
        self.payload = data.get("payload", {})
        self.partial = data.get("partial")  # this is deprecated, but leaving it for now
        self.partials = data.get("partials", [])

    def __repr__(self):
        return f"Action(action_type='{self.action_type}' payload={self.payload} partials={self.partials})"


def sort_dict(d):
    items = [[k, v] for k, v in sorted(d.items(), key=lambda x: x[0] if not is_int(x[0]) else int(x[0]))]

    for item in items:
        if isinstance(item[1], dict):
            item[1] = sort_dict(item[1])

    return dict(items)


class ComponentRequest:
    """
    Parses, validates, and stores all of the data from the message request.
    """

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
        if not self.data is not None:
            raise AssertionError("Missing data")  # data could theoretically be {}

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
            # TODO: Raise specific exception
            raise AssertionError("Missing meta")

        generated_checksum = generate_checksum(self.data)

        if meta != generated_checksum:
            # TODO: Raise specific exception
            raise AssertionError("Checksum does not match")


class Return:
    def __init__(self, method_name, args=None, kwargs=None):
        self.method_name = method_name
        self.args = args or []
        self.kwargs = kwargs or {}
        self._value = {}
        self.redirect = {}
        self.poll = {}

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        # TODO: Support a tuple/list return_value which could contain multiple values

        if value is not None:
            if isinstance(value, HttpResponseRedirect):
                self.redirect = {
                    "url": value.url,
                }
            elif isinstance(value, HashUpdate):
                self.redirect = {
                    "hash": value.hash,
                }
            elif isinstance(value, LocationUpdate):
                self.redirect = {
                    "url": value.redirect.url,
                    "refresh": True,
                    "title": value.title,
                }
            elif isinstance(value, PollUpdate):
                self.poll = value.to_json()

            if self.redirect:
                self._value = self.redirect

    def get_data(self):
        try:
            serialized_value = loads(dumps(self.value))
            serialized_args = loads(dumps(self.args))
            serialized_kwargs = loads(dumps(self.kwargs))

            return {
                "method": self.method_name,
                "args": serialized_args,
                "kwargs": serialized_kwargs,
                "value": serialized_value,
            }
        except Exception as e:
            logger.exception(e)

        return {}
