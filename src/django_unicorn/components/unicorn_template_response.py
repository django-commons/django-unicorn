import logging
import re
from collections import deque

import orjson
from django.conf import settings
from django.template.backends.django import Template
from django.template.response import TemplateResponse
from lxml import html

from django_unicorn.decorators import timed
from django_unicorn.errors import (
    MissingComponentElementError,
    MissingComponentViewElementError,
    MultipleRootComponentElementError,
    NoRootComponentElementError,
)
from django_unicorn.settings import get_minify_html_enabled
from django_unicorn.utils import generate_checksum, html_element_to_string

logger = logging.getLogger(__name__)


# https://developer.mozilla.org/en-US/docs/Glossary/Empty_element
EMPTY_ELEMENTS = (
    "<area>",
    "<base>",
    "<br>",
    "<col>",
    "<embed>",
    "<hr>",
    "<img>",
    "<input>",
    "<link>",
    "<meta>",
    "<param>",
    "<source>",
    "<track>",
    "<wbr>",
)


def is_html_well_formed(html_content: str) -> bool:
    """
    Whether the passed-in HTML is missing any closing elements which can cause issues when rendering.
    """

    tag_list = re.split("(<[^>!]*>)", html_content)[1::2]
    stack: deque[str] = deque()

    for tag in tag_list:
        if "/" not in tag:
            cleaned_tag = re.sub(r"(<([\w\-]+)[^>!]*>)", r"<\2>", tag)

            if cleaned_tag not in EMPTY_ELEMENTS:
                stack.append(cleaned_tag)
        elif len(stack) > 0 and (tag.replace("/", "") == stack[len(stack) - 1]):
            stack.pop()

    return len(stack) == 0


def get_root_element(content: str) -> html.HtmlElement:
    """Gets the first tag element for the component or the first element with a `unicorn:view` attribute for a direct
    view.

    Returns:
        lxml element.

        Raises `Exception` if an element cannot be found.
    """
    try:
        if isinstance(content, html.HtmlElement):
            return content

        if "<html" in content.lower():
            root_element = html.fromstring(content)
        else:
            # lxml.html.fragments_fromstring returns a list of elements/strings
            fragments = html.fragments_fromstring(content)
            elements = [f for f in fragments if isinstance(f, html.HtmlElement)]

            if not elements:
                raise MissingComponentElementError("No root element for the component was found")

            root_element = elements[0]
    except MissingComponentViewElementError:
        # Re-raise this specific error
        raise
    except Exception as e:
        if isinstance(e, MissingComponentElementError):
            raise
        raise MissingComponentElementError(f"Failed to parse component HTML: {e}") from e

    if root_element.tag == "html":
        # Check for unicorn:view in descendants
        view_element = None
        for element in root_element.iter():
            if "unicorn:view" in element.attrib or "u:view" in element.attrib:
                view_element = element
                break

        if view_element is None:
            raise MissingComponentViewElementError(
                "An element with an `unicorn:view` attribute is required for a direct view"
            )
        return view_element

    return root_element


def assert_has_single_wrapper_element(content: str, component_name: str) -> None:
    """Assert that there is only one root element."""
    try:
        if isinstance(content, html.HtmlElement):
            elements = [content]
        else:
            fragments = html.fragments_fromstring(content)
            elements = [f for f in fragments if isinstance(f, html.HtmlElement)]
    except Exception:
        # Should have been caught by get_root_element usually
        return

    # Check if any element has unicorn:view or u:view - these are direct views
    # and should skip the multiple root check
    for element in elements:
        has_view = "unicorn:view" in element.attrib or "u:view" in element.attrib
        has_poll = "unicorn:poll" in element.attrib or "u:poll" in element.attrib

        if has_view or (has_view and has_poll):
            # If the root element is a direct view (with or without poll), skip the check
            return

    if len(elements) > 1:
        raise MultipleRootComponentElementError(
            f"The '{component_name}' component appears to have multiple root elements."
        )

    if not elements:
        raise NoRootComponentElementError(f"The '{component_name}' component does not appear to have one root element.")

    if f"<{elements[0].tag}>" in EMPTY_ELEMENTS:
        raise NoRootComponentElementError(
            f"The '{component_name}' component root element cannot be a void element like <{elements[0].tag}>. "
            "It must be a wrapping element."
        )


class UnicornTemplateResponse(TemplateResponse):
    def __init__(
        self,
        template,
        request,
        *,
        context=None,
        content_type=None,
        status=None,
        charset=None,
        using=None,
        component=None,
        init_js=False,
        epoch="",
        **kwargs,  # noqa: ARG002
    ):
        super().__init__(
            template=template,
            request=request,
            context=context,
            content_type=content_type,
            status=status,
            charset=charset,
            using=using,
        )

        self.component = component
        self.init_js = init_js
        self.epoch = epoch or ""

    def resolve_template(self, template):
        """Override the TemplateResponseMixin to resolve a list of Templates.

        Calls the super which accepts a template object, path-to-template, or list of paths if the first
        object in the sequence is not a Template.
        """

        if isinstance(template, list | tuple):
            if isinstance(template[0], Template):
                return template[0]

        return super().resolve_template(template)

    @timed
    def render(self):
        response = super().render()

        if not self.component or not self.component.component_id:
            return response

        content = response.content.decode("utf-8")

        # Only check if HTML is well-formed in DEBUG mode
        if settings.DEBUG and not is_html_well_formed(content):
            logger.warning(
                f"The HTML in '{self.component.component_name}' appears to be missing a closing tag. "
                "That can potentially cause errors in Unicorn."
            )

        try:
            assert_has_single_wrapper_element(content, self.component.component_name)
        except (NoRootComponentElementError, MultipleRootComponentElementError) as ex:
            logger.warning(ex)

        root_element = get_root_element(content)

        # Prepare Data
        frontend_context_variables = self.component.get_frontend_context_variables()
        frontend_context_variables_dict = orjson.loads(frontend_context_variables)
        data_checksum = generate_checksum(frontend_context_variables_dict)

        # Modify Attributes
        root_element.set("unicorn:id", self.component.component_id)
        if hasattr(self.component, "component_name"):
            root_element.set("unicorn:name", self.component.component_name)
        root_element.set("unicorn:key", str(self.component.component_key or ""))
        root_element.set("unicorn:data", frontend_context_variables)
        root_element.set("unicorn:calls", orjson.dumps(self.component.calls).decode("utf-8"))

        # Calculate content hash (without script and without checksum)
        rendered_template_no_script = html_element_to_string(root_element)
        content_hash = generate_checksum(rendered_template_no_script)
        self.component._content_hash = content_hash

        # Set the data checksum on the root element
        root_element.set("unicorn:meta", data_checksum)

        rendered_template = html_element_to_string(root_element)

        self.component.rendered(rendered_template)
        response.content = rendered_template

        if get_minify_html_enabled():
            from htmlmin import minify  # noqa: PLC0415  # type: ignore

            minified_html = minify(response.content.decode())
            if len(minified_html) < len(rendered_template):
                response.content = minified_html

        return response
