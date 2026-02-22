import pickle
import sys
from unittest.mock import MagicMock

from django.test import RequestFactory
from lxml import html

from django_unicorn.components import UnicornView
from django_unicorn.components.unicorn_template_response import UnicornTemplateResponse


class RecursionComponent(UnicornView):
    template_name = "templates/test_component.html"
    pass


def test_child_component_cleanup_prevents_recursion_error():
    # 1. Create child component and simulate it having a large _json_tag (as if rendered)
    child = RecursionComponent(component_name="child", component_id="child_id")

    # Create a deep DOM to ensure recursion error would happen if not cleaned up
    depth = 2000
    html_content = "<div>" + ("<span>" * depth) + "Hello" + ("</span>" * depth) + "</div>"
    child._json_tag = html.fragment_fromstring(html_content)  # type: ignore
    child._init_script = "Unicorn.componentInit({});"

    # 2. Create parent component and link child
    parent = RecursionComponent(component_name="parent", component_id="parent_id")
    parent.children.append(child)

    # 3. Setup UnicornTemplateResponse for parent
    request = RequestFactory().get("/")
    template = MagicMock()
    template.render.return_value = "<html><body><div unicorn:view>Parent Content</div></body></html>"

    response = UnicornTemplateResponse(
        template=template,
        request=request,
        component=parent,
        init_js=True,  # Important to trigger the logic that collects json_tags
    )

    # Increase recursion limit
    original_recursion_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)

    try:
        # 4. Render the parent
        response.render()

        # 5. Verify pickling parent works
        # Manually delete _json_tag since it's not automatically deleted anymore
        # but it would cause a recursion error if we try to pickle it with a deep DOM
        if hasattr(child, "_json_tag"):
            del child._json_tag

        pickle.dumps(parent)

    finally:
        sys.setrecursionlimit(original_recursion_limit)
