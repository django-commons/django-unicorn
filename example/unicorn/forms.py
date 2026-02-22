from django import forms

from example.coffee.models import Document


class ValidationForm(forms.Form):
    text = forms.CharField(min_length=3, max_length=10)
    date_time = forms.DateTimeField()
    number = forms.IntegerField()
    email = forms.EmailField()


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("document",)
