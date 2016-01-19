from django import forms
import datetime



class SearchForm(forms.Form):
    block_name = forms.CharField(max_length=150, required=False)
    department_name = forms.CharField(max_length=150, required=False)
    drawing_name  = forms.CharField(max_length=250, required=False)
    revision_number = forms.CharField(max_length=100, required=False)
    drawing_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=(('review', 'New/Review'),
                                                ('approved', 'Final/Approved')))
    comment_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=(('open', 'Open'),
                                                ('closed', 'Closed')))

