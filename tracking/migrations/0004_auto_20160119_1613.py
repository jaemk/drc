# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-19 16:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0003_auto_20160118_2202'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='attachments',
            field=models.FileField(blank=True, upload_to='uploads/comments'),
        ),
        migrations.AddField(
            model_name='drawing',
            name='attachments',
            field=models.FileField(blank=True, upload_to='uploads/drawings'),
        ),
        migrations.AddField(
            model_name='reply',
            name='attachments',
            field=models.FileField(blank=True, upload_to='uploads/replies'),
        ),
        migrations.AddField(
            model_name='revision',
            name='attachments',
            field=models.FileField(blank=True, upload_to='uploads/revisions'),
        ),
    ]
