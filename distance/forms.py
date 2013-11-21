from django import forms

class PostcodeForm(forms.Form):
    postcode = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size':'10'}))


class LLForm(forms.Form):
    latitude = forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}))
    longitude = forms.DecimalField(widget=forms.TextInput(attrs={'size':'10'}))
