"""
Django signals for django-unicorn component lifecycle events.

All signals are sent with ``sender=component.__class__`` and at minimum a
``component`` kwarg containing the live ``UnicornView`` instance.  Connect a
receiver to observe events without monkey-patching internal methods:

    from django.dispatch import receiver
    from django_unicorn.signals import component_rendered

    @receiver(component_rendered)
    def on_render(sender, component, html, **kwargs):
        print(f"{component.component_name} rendered {len(html)} bytes")
"""

from django.dispatch import Signal

component_mounted = Signal()

component_hydrated = Signal()

component_completed = Signal()

component_rendered = Signal()

component_parent_rendered = Signal()

component_property_updating = Signal()

component_property_updated = Signal()

component_property_resolved = Signal()

component_method_calling = Signal()

component_method_called = Signal()

component_pre_parsed = Signal()

component_post_parsed = Signal()
