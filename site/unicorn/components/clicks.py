from django_unicorn.components import UnicornView


class ClicksView(UnicornView):
    count = 0

    def add(self):
        self.count += 1

    def subtract(self):
        self.count -= 1
