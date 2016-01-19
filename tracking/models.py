from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime


class Block(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<Block: {}>'.format(self.name)

    def __str__(self):
        return 'Block: {}'.format(self.name.upper())


class DrawingStatus(models.Model):
    status = models.CharField(max_length=150)

    def __repr__(self):
        return '<DwgStatus: {}>'.format(self.status)

    def __str__(self):
        return 'DwgStatus: {}'.format(self.status.title())


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
        return 'Discip: {}'.format(self.name.title())


class DrawingKind(models.Model):
    name = models.CharField(max_length=150)

    def __repr__(self):
        return '<DwgKind: {}>'.format(self.name)

    def __str__(self):
        return 'DwgKind: {}'.format(self.name.title())


class Drawing(models.Model):
    name = models.CharField(max_length=250)
    desc = models.CharField(max_length=500, blank=True, null=True)
    phase = models.CharField(max_length=25, blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.SET_NULL,
                              blank=True, null=True)
    status = models.ForeignKey(DrawingStatus, on_delete=models.SET_NULL,
                               blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL,
                                    blank=True, null=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.SET_NULL,
                                    blank=True, null=True)
    kind = models.ForeignKey(DrawingKind, on_delete=models.SET_NULL,
                                    blank=True, null=True)
    attachments = models.FileField(upload_to='uploads/drawings',
                                   blank=True) # default='settings.BASE_DIR/pdfs/file.pdf')
    
    # date stuff
    expected = models.DateTimeField(null=True)
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     blank=True, null=True)

    def __repr__(self):
        return '<Drawing: {}>'.format(self.name)

    def __str__(self):
        return 'Drawing: {}'.format(self.name.upper())

    def newest_rev(self):
        ''' Return most recent revision object '''
        pass

    def revisions(self):
        ''' Return all revision objects '''
        pass


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
        return 'Rev: {} on dwg: {}'.format(self.number.upper(), self.drawing.name.upper())

    def newest_comment(self):
        ''' Return most recent comment '''
        pass

    def comments(self):
        ''' Return all comment objects '''
        pass


class Comment(models.Model):
    desc = models.CharField(max_length=500, blank=True, null=True)
    text = models.CharField(max_length=1000, blank=True, null=True)
    status = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='comment_owner',
                              blank=True, null=True)
    revision = models.ForeignKey(Revision, on_delete=models.SET_NULL,
                                 blank=True, null=True)
    attachments = models.FileField(upload_to='uploads/comments',
                                   blank=True)

    # date stuff
    add_date = models.DateTimeField(auto_now=True)
    mod_date = models.DateTimeField(auto_now=True, null=True)
    mod_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                               related_name='comment_mod_by',
                               blank=True, null=True)

    def __repr__(self):
        return '<Comm: {} on {}>'.format(self.id, self.revision)

    def __str__(self):
        return 'Comment by {} on - {}'.format(self.owner, self.revision)


class Reply(models.Model):
    desc = desc = models.CharField(max_length=500, blank=True, null=True)
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

    def __repr__(self):
        return '<Reply: {} on com. {}>'.format(self.id, self.comment)

    def __str__(self):
        return 'Reply to: {}'.format(self.comment)
