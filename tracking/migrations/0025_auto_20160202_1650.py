# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-02 16:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0024_auto_20160202_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drawingsubscription',
            name='last_mod_date',
            field=models.DateTimeField(null=True),
        ),
    ]
