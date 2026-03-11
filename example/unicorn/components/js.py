from django.utils.timezone import now

from django_unicorn.components import UnicornView


class JsView(UnicornView):
    states = (
        "Alabama",
        "Alaska",
        "Wisconsin",
        "Wyoming",
    )
    selected_state = ""
    select2_datetime = now()
    scroll_counter = 0
    load_js = False

    def call_javascript(self):
        self.call("Unicorn.callAlert", "world")

    def call_javascript_module(self):
        self.call("HelloJs.hello", "world!")

    def get_now(self):
        self.select2_datetime = now()

    def change_states(self):
        self.states = ("Pennsylvania",)

    def select_state(self, val, idx):
        print("select_state called", val)
        print("select_state called idx", idx)
        self.selected_state = val

    def increase_counter(self):
        if self.scroll_counter >= 2:
            return False

        self.scroll_counter += 1

    class Meta:
        javascript_exclude = ("states",)
