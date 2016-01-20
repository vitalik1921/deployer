from django.contrib import admin
from django.contrib.sites.models import Site

from .models import Listeners, FTPServers, Emails


@admin.register(Listeners)
class ListenerAdmin(admin.ModelAdmin):
    list_display = ['repository_slug', 'development_server', 'production_server']
    fields = ['repository_url', 'get_full_url',
        'repository_slug', 'repository_owner', 'development_branch', 'development_server',
        'development_server_path', 'production_branch', 'production_server', 'production_server_path', 'emails']

    readonly_fields = ['repository_url', 'get_full_url']


@admin.register(FTPServers)
class FTPServerAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Emails)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['name']