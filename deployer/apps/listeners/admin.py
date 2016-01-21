from django.contrib import admin
from .models import Listeners, FTPServers, Logs, Emails


@admin.register(Listeners)
class ListenerAdmin(admin.ModelAdmin):
    def get_listener_log(self, obj):
        log = Logs.objects.filter(listener_id=obj.listener_uuid).order_by('datetime')
        text = ''
        for item in log:
            text += "({}) {} \n".format(item.datetime, item.message)
        return "<textarea disabled style='width:64%; height:400px'>{}</textarea>".format(text)

    get_listener_log.short_description = 'Log'
    get_listener_log.allow_tags = True

    list_display = ['repository_slug', 'development_server', 'production_server']
    fields = ['repository_url', 'get_full_url',
              'repository_slug', 'repository_owner',
              'enable_development',
              ('development_server', 'development_branch', 'development_server_path'),
              'enable_production',
              ('production_server', 'production_branch', 'production_server_path'),
              'emails', 'get_listener_log']

    readonly_fields = ['repository_url', 'get_full_url', 'get_listener_log']


@admin.register(FTPServers)
class FTPServerAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Emails)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['name']
