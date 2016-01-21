from django import forms
import datetime


class SearchForm(forms.Form):
    drawing_name  = forms.CharField(max_length=250, required=True)
    revision_number = forms.CharField(max_length=100, required=False)
    comment_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=((True, 'Open'),
                                                (False, 'Closed')))
    drawing_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=(('review', 'New/Review'),
                                                ('approved', 'Final/Approved')))
    block_name = forms.CharField(max_length=150, required=False)
    department_name = forms.CharField(max_length=150, required=False)


class FileForm(forms.Form):
    newfile = forms.FileField(label='Select a file',
                              help_text='pdfs prefered')

