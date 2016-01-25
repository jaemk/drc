from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime


class Project(models.Model):
    name = models.CharField(max_length=200)

    def __repr__(self):
        return '<Proj: {}'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name.upper())


class Block(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<Block: {}>'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name.upper())


class Phase(models.Model):
    number = models.CharField(max_length=25)

    def __repr__(self):
        return '<Phase: {}>'.format(self.number)

    def __str__(self):
        return '{}'.format(self.number)
    

class DrawingStatus(models.Model):
    status = models.CharField(max_length=150)

    def __repr__(self):
        return '<DwgStatus: {}>'.format(self.status)

    def __str__(self):
        return '{}'.format(self.status.title())


class Department(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<Dep.: {}>'.format(self.name)

    def __str__(self):
        return 'Dep: {}'.format(self.name)


class Discipline(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<Disc.: {}>'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name.title())


class DrawingKind(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<DwgKind: {}>'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name.title())


class Drawing(models.Model):
    name = models.CharField(max_length=250)
    desc = models.CharField(max_length=500, blank=True, null=True)
    phase = models.ForeignKey(Phase, on_delete=models.SET_NULL, null=True)
    received = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL,
                                null=True)
    block = models.ManyToManyField(Block)
    status = models.ForeignKey(DrawingStatus, on_delete=models.SET_NULL,
                               blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                    blank=True, null=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.SET_NULL,
                                    blank=True, null=True)
    kind = models.ForeignKey(DrawingKind, on_delete=models.SET_NULL,
                                    blank=True, null=True)

    expected = models.DateTimeField(null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     blank=True, null=True)

    def __repr__(self):
        return '<Drawing: {}>'.format(self.name)

    def __str__(self):
        return '{}'.format(self.name.upper())

    def newest_rev(self):
        ''' Return most recent revision object '''
        pass

    def revisions(self):
        ''' Return all revision objects '''
        pass


def drawing_upload_path(instance, filename):
    # upload to MEDIA_ROOT/drawing/<filename>
    # time = timezone.now()
    # time.strftime('%m-%d-%Y_%H.%M.%S')
    # print(instance.__dict__)
    if getattr(instance, 'drawing_id', None):
        print('drawing: {}'.format(instance.drawing_id))
        return 'drawing/{}'.format(filename)
    if getattr(instance, 'revision_id', None):
        print('revision: {}'.format(instance.revision_id))
        return 'revision/{}'.format(filename)
    if getattr(instance, 'comment_id', None):
        print('comment: {}'.format(instance.comment_id))
        return 'comment/{}'.format(filename)
    if getattr(instance, 'reply_id', None):
        print('reply: {}'.format(instance.reply_id))
        return 'reply/{}'.format(filename)
    

class DrawingAttachment(models.Model):
    upload = models.FileField(upload_to=drawing_upload_path,
                              blank=True) # default='settings.BASE_DIR/pdfs/file.pdf')
    drawing = models.ForeignKey(Drawing, on_delete=models.SET_NULL,
                                blank=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                blank=True, null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)

    def filename(self, filepath=None):
        if not filepath:
            filepath = self.upload.name
        return filepath.split('/')[-1]

    def __repr__(self):
        return '<Attachment: {}>'.format(self.upload)

    def __str__(self):
        return 'Att: {}'.format(self.filename())


class Revision(models.Model):
    number = models.CharField(max_length=100)
    desc = models.CharField(max_length=500, blank=True, null=True)
    drawing = models.ForeignKey(Drawing, on_delete=models.SET_NULL,
                                blank=True, null=True)
    attachments = models.FileField(upload_to='uploads/revisions',
                                   blank=True)

    # date stuff
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     blank=True, null=True)

    def __repr__(self):
        return '<Rev: {} on {}>'.format(self.number, self.drawing.name)

    def __str__(self):
        return '{}:{}'.format(self.drawing.name.upper(), self.number.upper())

    def newest_comment(self):
        ''' Return most recent comment '''
        pass

    def comments(self):
        ''' Return all comment objects '''
        pass

class RevisionAttachment(models.Model):
    upload = models.FileField(upload_to=drawing_upload_path,
                              blank=True) # default='settings.BASE_DIR/pdfs/file.pdf')
    revision = models.ForeignKey(Revision, on_delete=models.SET_NULL,
                                blank=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                blank=True, null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)

    def filename(self, filepath=None):
        if not filepath:
            filepath = self.upload.name
        return filepath.split('/')[-1]

    def __repr__(self):
        return '<Attachment: {}>'.format(self.upload)

    def __str__(self):
        return 'Att: {}'.format(self.filename())


class Comment(models.Model):
    desc = models.CharField(max_length=500, blank=True, null=True)
    text = models.CharField(max_length=1000, blank=True, null=True)
    status = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='comment_owner',
                              blank=True, null=True)
    revision = models.ManyToManyField(Revision)
    attachments = models.FileField(upload_to='uploads/comments',
                                   blank=True)

    # date stuff
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                               related_name='comment_mod_by',
                               blank=True, null=True)

    def open_closed(self):
        if self.status:
            return 'Open'
        else:
            return 'Closed'

    def number_replies(self):
        return Reply.objects.filter(comment__id=self.id).count()

    def revisions(self):
        return '{}'.format(', '.join([str(rev) for rev in self.revision.all()]))

    def __repr__(self):
        return '<Comm: {} on {}>'.format(self.id, 
               ', '.join([str(rev) for rev in self.revision.all()]))

    def __str__(self):
        return 'Comment by {} on - {}'.format(self.owner,
               ' & '.join([str(rev) for rev in self.revision.all()]))


class CommentAttachment(models.Model):
    upload = models.FileField(upload_to=drawing_upload_path,
                              blank=True) # default='settings.BASE_DIR/pdfs/file.pdf')
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL,
                                blank=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                blank=True, null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)

    def filename(self, filepath=None):
        if not filepath:
            filepath = self.upload.name
        return filepath.split('/')[-1]

    def __repr__(self):
        return '<Attachment: {}>'.format(self.upload)

    def __str__(self):
        return 'Att: {}'.format(self.filename())


class Reply(models.Model):
    number = models.IntegerField(default=0)
    desc = models.CharField(max_length=500, blank=True, null=True)
    text = models.CharField(max_length=1000, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL,
                                blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='reply_owner',
                              blank=True, null=True)
    attachments = models.FileField(upload_to='uploads/replies',
                                   blank=True)

    # date stuff
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                               related_name='reply_mod_by',
                               blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Reply, self).__init__(*args, **kwargs)
        # self.number = self.comment.number_replies() + 1
        
    def __repr__(self):
        return '<Reply: {} on com. {}>'.format(self.id, self.comment)

    def __str__(self):
        return 'Reply to: {}'.format(self.comment)

class ReplyAttachment(models.Model):
    upload = models.FileField(upload_to=drawing_upload_path,
                              blank=True) # default='settings.BASE_DIR/pdfs/file.pdf')
    reply = models.ForeignKey(Reply, on_delete=models.SET_NULL,
                                blank=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                blank=True, null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)

    def filename(self, filepath=None):
        if not filepath:
            filepath = self.upload.name
        return filepath.split('/')[-1]

    def __repr__(self):
        return '<Attachment: {}>'.format(self.upload)

    def __str__(self):
        return 'Att: {}'.format(self.filename())