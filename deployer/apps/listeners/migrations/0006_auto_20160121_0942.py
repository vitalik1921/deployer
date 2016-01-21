# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-21 09:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('listeners', '0005_auto_20160121_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listeners',
            name='development_branch',
            field=models.CharField(blank=True, default='master', max_length=150),
        ),
        migrations.AlterField(
            model_name='listeners',
            name='development_server',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='listeners.FTPServers'),
        ),
        migrations.AlterField(
            model_name='listeners',
            name='development_server_path',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='listeners',
            name='production_branch',
            field=models.CharField(blank=True, default='production', max_length=150),
        ),
        migrations.AlterField(
            model_name='listeners',
            name='production_server',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='listeners.FTPServers'),
        ),
        migrations.AlterField(
            model_name='listeners',
            name='production_server_path',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]