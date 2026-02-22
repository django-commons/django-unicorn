from django.utils.timezone import now

from django_unicorn.components import UnicornView


class HelloWorldView(UnicornView):
    template_name = "unicorn/hello-world-test.html"

    name = "World"

    def set_name(self):
        self.name = "set_name method called"
        return "set_name called at " + now().strftime("%H:%M:%S.%f")

    @property
    def user(self):
        return self.request.user

    class Meta:
        javascript_exclude = (
            "user",
        )
