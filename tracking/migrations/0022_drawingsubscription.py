# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-02 15:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracking', '0021_auto_20160126_1641'),
    ]

    operations = [
        migrations.CreateModel(
            name='DrawingSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('drawing', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tracking.Drawing')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
