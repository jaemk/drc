from django import forms
from .models import Project
from .models import Phase
from .models import Block
from .models import Department
from .models import Discipline
from .models import DrawingKind
from .models import DrawingStatus
import datetime


class SearchForm(forms.Form):
    drawing_name  = forms.CharField(max_length=250, required=True)
    revision_number = forms.CharField(max_length=100, required=False)
    comment_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=(('open', 'Open'),
                                                ('closed', 'Closed')))
    drawing_status = forms.MultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       choices=(('review', 'New/Review'),
                                                ('approved', 'Final/Approved')))
    block_name = forms.CharField(max_length=150, required=False)
    department_name = forms.CharField(max_length=150, required=False)


class DrawingAddForm(forms.Form):
    name = forms.CharField(max_length=250, required=True)
    desc = forms.CharField(max_length=500, required=False)
    phase = forms.ModelChoiceField(queryset=Phase.objects.all(),
                                   to_field_name='number', required=False)
    received = forms.MultipleChoiceField(required=False,
                                         widget=forms.CheckboxSelectMultiple,
                                         choices=(('yes', 'Yes'),
                                                 ('no' , 'No')))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), 
                                     to_field_name='name', required=False)
    block = forms.ModelMultipleChoiceField(queryset=Block.objects.all(),
                                           to_field_name='name', required=False)
    status = forms.ModelChoiceField(queryset=DrawingStatus.objects.all(),
                                    to_field_name='status', required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(),
                                        to_field_name='name', required=False)
    discipline = forms.ModelChoiceField(queryset=Discipline.objects.all(),
                                        to_field_name='name', required=False)
    kind = forms.ModelChoiceField(queryset=DrawingKind.objects.all(),
                                    to_field_name='name', required=False)

    def __init__(self, edit=False, *args, **kwargs):
        super(DrawingAddForm, self).__init__(*args, **kwargs)
        if edit:
            self.fields['name'].required = False


class FileForm(forms.Form):
    newfile = forms.FileField(label='Select a file',
                              help_text='''<small>pdfs prefered<br/>
                                           all formats accepted<br/>
                                           only single file upload per submission</small>''')

