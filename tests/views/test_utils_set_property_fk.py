import pytest

from django_unicorn.views.utils import set_property_from_data
from example.coffee.models import Flavor


@pytest.mark.django_db
def test_set_property_fk_with_pk_int():
    # Arrange
    parent = Flavor.objects.create(name="Parent")
    child = Flavor.objects.create(name="Child")  # No parent initially

    # Act
    # Try to set the parent FK using the parent's PK (int)
    set_property_from_data(child, "parent", parent.pk)

    # Assert
    assert child.parent_id == parent.pk


@pytest.mark.django_db
def test_set_property_fk_with_pk_str():
    # Arrange
    parent = Flavor.objects.create(name="Parent")
    child = Flavor.objects.create(name="Child")

    # Act
    # Try to set the parent FK using the parent's PK (str)
    # Frontend might send ID as string
    set_property_from_data(child, "parent", str(parent.pk))

    # Assert
    assert str(child.parent_id) == str(parent.pk)


@pytest.mark.django_db
def test_set_property_fk_with_model_instance():
    # Arrange
    parent = Flavor.objects.create(name="Parent")
    child = Flavor.objects.create(name="Child")

    # Act
    set_property_from_data(child, "parent", parent)

    # Assert
    assert child.parent == parent
    assert child.parent_id == parent.pk


@pytest.mark.django_db
def test_set_property_fk_none():
    # Arrange
    parent = Flavor.objects.create(name="Parent")
    child = Flavor.objects.create(name="Child", parent=parent)

    # Act
    set_property_from_data(child, "parent", None)

    # Assert
    assert child.parent_id is None
    assert child.parent is None


@pytest.mark.django_db
def test_set_property_fk_invalid_field_ignored():
    # Arrange
    child = Flavor.objects.create(name="Child")

    # Act
    # Should not raise error
    set_property_from_data(child, "non_existent_field", 123)


@pytest.mark.django_db
def test_set_property_non_fk_field():
    # Arrange
    child = Flavor.objects.create(name="Child")

    # Act
    set_property_from_data(child, "name", "Updated Name")

    # Assert
    assert child.name == "Updated Name"
