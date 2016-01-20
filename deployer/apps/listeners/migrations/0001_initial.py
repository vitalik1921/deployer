# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-19 08:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Emails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=150)),
                ('email', models.EmailField(max_length=150)),
            ],
            options={
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
            },
        ),
        migrations.CreateModel(
            name='FTPServers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=150)),
                ('host', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=100)),
                ('password', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'FTPServer',
                'verbose_name_plural': 'FTPServers',
            },
        ),
        migrations.CreateModel(
            name='Listeners',
            fields=[
                ('repository_uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('repository_slug', models.CharField(max_length=255, unique=True)),
                ('repository_owner', models.CharField(max_length=150)),
                ('development_branch', models.CharField(default='master', max_length=150)),
                ('development_server_path', models.CharField(max_length=500)),
                ('production_branch', models.CharField(default='production', max_length=150)),
                ('production_server_path', models.CharField(max_length=500)),
                ('development_server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='listeners.FTPServers')),
                ('emails', models.ManyToManyField(blank=True, related_name='_listeners_emails_+', to='listeners.Emails')),
                ('production_server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='listeners.FTPServers')),
            ],
            options={
                'verbose_name': 'Listener',
                'verbose_name_plural': 'Listeners',
            },
        ),
        migrations.CreateModel(
            name='Logs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField()),
                ('reported', models.BooleanField()),
                ('listener', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='listeners.Listeners')),
            ],
        ),
    ]