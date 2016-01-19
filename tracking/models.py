from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime


class Block(models.Model):
    name = models.CharField(max_length=150)


class DrawingStatus(models.Model):
    status = models.CharField(max_length=150)


class Department(models.Model):
    name = models.CharField(max_length=150)


class Discipline(models.Model):
    name = models.CharField(max_length=150)


class DrawingKind(models.Model):
    name = models.CharField(max_length=150)


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

    def newest_comment(self):
        ''' Return most recent comment '''
        pass

    def comments(self):
        ''' Return all comment objects '''
        pass


class Comment(models.Model):
    desc = models.CharField(max_length=500, blank=True, null=True)
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


class Reply(models.Model):
    desc = desc = models.CharField(max_length=500, blank=True, null=True)
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

