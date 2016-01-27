from django import forms
# from django.contrib.admin.widgets import AdminDateWidget
from .models import Project
from .models import Phase
from .models import Block
from .models import Department
from .models import Discipline
from .models import DrawingKind
from .models import DrawingStatus
from .models import Drawing
from .models import Revision
from .models import Comment
from .models import Reply
from .models import DrawingAttachment
from .models import RevisionAttachment
from .models import CommentAttachment
from .models import ReplyAttachment
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
    received = forms.ChoiceField(required=False,
                                         widget=forms.Select,
                                         choices=((None, '--'),
                                                  ('no', 'No'),
                                                  ('yes' , 'Yes')))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), 
                                     to_field_name='name', required=False)
    block = forms.ModelMultipleChoiceField(queryset=Block.objects.all(),
                                           to_field_name='name', required=False,
                                           help_text='''<small>ctrl+click 
                                                        to select multiple</small>''')
    status = forms.ModelChoiceField(queryset=DrawingStatus.objects.all(),
                                    to_field_name='status', required=False)
    expected = forms.DateField(widget=forms.SelectDateWidget(
                                            empty_label=('Year', 'Month', 'Day')),
                                            required=False)
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


class RevisionAddForm(forms.Form):
    number = forms.CharField(max_length=100, required=True)
    desc = forms.CharField(max_length=500, required=False)
    drawing = forms.ModelChoiceField(queryset=Drawing.objects.all().order_by('name'),
                                     to_field_name='name', required=True)
    add_date = forms.DateField(widget=forms.SelectDateWidget(
                                            empty_label=('Year', 'Month', 'Day')),
                                            required=False,
                                            help_text='''<small>defaults to today</small>''')
    
    def __init__(self, drawing_name=None, *args, **kwargs):
        super(RevisionAddForm, self).__init__(*args, **kwargs)
        if drawing_name:
            self.fields['drawing'].queryset = Drawing.objects.filter(name=drawing_name)


class FileForm(forms.Form):
    newfile = forms.FileField(label='Select a file',
                              help_text='''<small>pdfs prefered<br/>
                                           all formats accepted<br/>
                                           only single file upload per submission</small>''')


def _get_file_set(item_type, item_id):
    ''' fetch the set of attachments for specified item '''
    attch = {'drawing':DrawingAttachment, 'revision':RevisionAttachment,
             'comment':CommentAttachment, 'reply':ReplyAttachment}
    table = {'drawing':Drawing, 'revision':Revision,
             'comment':Comment, 'reply':Reply}

    obj = table[item_type].objects.get(pk=item_id)
    attachments = attch[item_type].objects.filter(link=obj)
    return attachments


class RemoveFileForm(forms.Form):
    def __init__(self, item_type=None, item_id=None, *args, **kwargs):
        if not item_type or not item_id:
            return    
        super(RemoveFileForm, self).__init__(*args, **kwargs)
        queryset = _get_file_set(item_type, item_id)
        self.fields['files'] = forms.ModelMultipleChoiceField(required=False,
                                       widget=forms.CheckboxSelectMultiple,
                                       queryset=queryset,
                                       label='Select files to remove',
                                       help_text='<small>select multiple to delete</small>')
                                       # choices=(('backend', 'Shown'),
                                       #          ('backend', 'Shown')))



