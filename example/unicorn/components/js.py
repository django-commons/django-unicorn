from django.utils.timezone import now

from django_unicorn.components import UnicornView

from ..forms import DocumentForm


class JsView(UnicornView):
    form_class = DocumentForm

    document = None
    upload_success = False
    uploaded_filename = ""

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
        self.call("callAlert", "world")

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

    def upload_file(self):
        self.upload_success = False
        self.uploaded_filename = ""
        if self.is_valid():
            instance = self.form.save()
            self.uploaded_filename = instance.document.name
            self.upload_success = True
            self.document = None  # clear the file input after a successful save

    class Meta:
        javascript_excludes = ("states",)
