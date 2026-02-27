from django_unicorn.components import UnicornView

class TransitionView(UnicornView):
    show = False

    def toggle(self):
        self.show = not self.show
