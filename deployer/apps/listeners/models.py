import uuid

from django.db import models
from django.contrib.sites.models import Site

from deployer.settings.base import GIT_USER_NAME, GIT_USER_PASS


class Listeners(models.Model):
    listener_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository_url = models.CharField(max_length=500, blank=True, editable=False)
    repository_slug = models.CharField(max_length=255, blank=False, unique=True)
    repository_owner = models.CharField(max_length=150, blank=False)
    development_branch = models.CharField(max_length=150, blank=False, default='master')
    development_server = models.ForeignKey('FTPServers', related_name='+')
    development_server_path = models.CharField(max_length=500, blank=False)
    production_branch = models.CharField(max_length=150, blank=False, default='production')
    production_server = models.ForeignKey('FTPServers', related_name='+')
    production_server_path = models.CharField(max_length=500, blank=False)
    emails = models.ManyToManyField('Emails', related_name='+', blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.repository_url:
            self.repository_url = 'https://{}:{}@bitbucket.org/{}/{}.git'.format(GIT_USER_NAME, GIT_USER_PASS,
                                                                        self.repository_owner, self.repository_slug)

        super().save(force_insert, force_update, using, update_fields)

    def get_full_url(self):
        from django.core.urlresolvers import reverse
        return Site.objects.get_current().domain + reverse('webhook', args={self.listener_uuid})

    get_full_url.short_description = 'Listener URL (just for bitbucket)'

    def __str__(self):
        return self.repository_slug

    class Meta:
        verbose_name = 'Listener'
        verbose_name_plural = 'Listeners'


class FTPServers(models.Model):
    name = models.CharField(max_length=150, blank=True)
    host = models.CharField(max_length=255, blank=False)
    username = models.CharField(max_length=100, blank=False)
    password = models.CharField(max_length=100, blank=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name:
            self.name = self.address
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'FTPServer'
        verbose_name_plural = 'FTPServers'


class Emails(models.Model):
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=150, blank=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.name:
            self.name = self.email
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Email'
        verbose_name_plural = 'Emails'


class Logs(models.Model):
    listener = models.ForeignKey(Listeners, related_name='logs')
    datetime = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    reported = models.BooleanField()

    def save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.reported:
            # TODO: Send email
            pass
        super().save_base(raw, force_insert, force_update, using, update_fields)

    @classmethod
    def create_record(cls, listener, message, report=False):
        record = cls(listener=listener, message=message, reported=report)
        record.save()
        return record
