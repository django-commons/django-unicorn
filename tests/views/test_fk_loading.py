import pytest
from tests.views.message.utils import post_and_get_response

from django_unicorn.components import UnicornView
from example.coffee.models import Flavor


class TestIssue732View(UnicornView):
    template_name = "templates/test_component.html"
    flavor: Flavor | None = None

    def mount(self):
        pass

    def load_flavor(self, flavor_id):
        self.flavor = Flavor.objects.get(pk=flavor_id)

    def save(self):
        self.flavor.save()


@pytest.mark.django_db
def test_fk_loading(client):
    # Setup
    parent_flavor = Flavor.objects.create(name="Parent")
    child_flavor = Flavor.objects.create(name="Child", parent=parent_flavor)

    # 1. Execute 'load_flavor'
    action_queue = [
        {
            "payload": {"name": f"load_flavor({child_flavor.pk})"},
            "type": "callMethod",
        }
    ]
    response = post_and_get_response(
        client,
        url="/message/tests.views.test_fk_loading.TestIssue732View",
        action_queue=action_queue,
    )

    assert not response.get("error")
    data = response["data"]

    # Verify flavor is in data
    assert "flavor" in data
    assert data["flavor"]["pk"] == child_flavor.pk

    # 2. Execute 'save' with the returned data
    action_queue = [
        {
            "payload": {"name": "save", "args": []},
            "type": "callMethod",
        }
    ]

    # This is where it should fail without the fix
    response = post_and_get_response(
        client,
        url="/message/tests.views.test_fk_loading.TestIssue732View",
        data=data,
        action_queue=action_queue,
    )

    assert not response.get("error")
