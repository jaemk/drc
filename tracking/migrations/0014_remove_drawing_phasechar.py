# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-22 02:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0013_drawing_phase'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='drawing',
            name='phasechar',
        ),
    ]