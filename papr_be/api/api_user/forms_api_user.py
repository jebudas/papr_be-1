
from django import forms

class FormInviteRequest(forms.Form):
    email = forms.EmailField(label='enter email', max_length=100)
