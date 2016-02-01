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
    
    def __init__(self, drawing_name=None, edit=False, *args, **kwargs):
        super(RevisionAddForm, self).__init__(*args, **kwargs)
        if drawing_name:
            self.fields['drawing'].queryset = Drawing.objects.filter(name=drawing_name)
        if edit:
            self.fields['number'].required = False
            del self.fields['drawing']
            del self.fields['add_date']


class CommentAddForm(forms.Form):
    revision = forms.ModelMultipleChoiceField(queryset=None,
                                             to_field_name='number', 
                                             required=True,
                                             help_text='''<small>hold ctrl to select 
                                                          multiple</small>''')
    desc = forms.CharField(max_length=500, required=True)
    text = forms.CharField(max_length=1000, required=True,
                           widget=forms.Textarea)
    status = forms.ChoiceField(required=False,
                               help_text='<small>defaults to open</small>',
                               widget=forms.Select,
                               choices=((None, '--'),
                               ('open', 'Open'),
                               ('closed' , 'Closed'))) 
    
    def __init__(self, drawing_name=None, edit=False, *args, **kwargs):
        super(CommentAddForm, self).__init__(*args, **kwargs)
        if drawing_name:
            dwg = Drawing.objects.get(name=drawing_name)
            self.fields['revision'].queryset = Revision.objects.filter(drawing=dwg)\
                                                               .order_by('number')

        if edit:
            self.fields['revision'].queryset = Revision.objects.all()
            self.fields['revision'].required = False
            self.fields['desc'].required = False
            self.fields['text'].required = False
            self.fields['status'].help_text = None


class ReplyAddForm(forms.Form):
    # ModelChoiceField(queryset=Drawing.objects.all().order_by('name'),
    #                                  to_field_name='name', required=True)
    # comment = forms.ModelChoiceField(queryset=None,
    #                                          to_field_name='number', 
    #                                          required=True,
    #                                          help_text='''<small>select 
    #                                                       multiple </small>''')
    desc = forms.CharField(max_length=500, required=True)
    text = forms.CharField(max_length=1000, required=True,
                           widget=forms.Textarea)
    # status = forms.ChoiceField(required=False,
    #                            help_text='<small>defaults to open</small>',
    #                            widget=forms.Select,
    #                            choices=((None, '--'),
    #                            ('open', 'Open'),
    #                            ('closed' , 'Closed'))) 
    
    def __init__(self, edit=False, *args, **kwargs):
        super(ReplyAddForm, self).__init__(*args, **kwargs)
        if edit:
            self.fields['desc'].required = False
            self.fields['text'].required = False



class FileForm(forms.Form):
    newfile = forms.FileField(label='Select a file',
                              help_text='''<small>pdfs prefered<br/>
                                           all formats accepted<br/>
                                           only single file upload per 
                                           submission</small>''')


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



