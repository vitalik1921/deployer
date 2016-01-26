import uuid

from django.db import models
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail

from deployer.settings.base import GIT_USER_NAME, GIT_USER_PASS, EMAIL_HOST_USER


class Listeners(models.Model):
    listener_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository_url = models.CharField(max_length=500, blank=True, editable=False)
    repository_slug = models.CharField(max_length=255, blank=False, unique=True)
    repository_owner = models.CharField(max_length=150, blank=False)
    enable_development = models.BooleanField()
    development_branch = models.CharField(max_length=150, blank=True, default='master')
    development_server = models.ForeignKey('FTPServers', related_name='+', blank=True, null=True)
    development_server_path = models.CharField(max_length=500, blank=True)
    enable_production = models.BooleanField()
    production_branch = models.CharField(max_length=150, blank=True, default='production')
    production_server = models.ForeignKey('FTPServers', related_name='+', blank=True, null=True)
    production_server_path = models.CharField(max_length=500, blank=True)
    emails = models.ManyToManyField('Emails', related_name='+', blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.repository_url = 'https://{}:{}@bitbucket.org/{}/{}.git'.format(GIT_USER_NAME, GIT_USER_PASS,
                                                                             self.repository_owner,
                                                                             self.repository_slug)

        super().save(force_insert, force_update, using, update_fields)

    def clean_fields(self, exclude=None):
        if self.enable_development:
            if not self.development_branch or not self.development_server or not self.development_server_path:
                raise ValidationError(
                    'Missed fields development_branch, development_server, development_server_path ')

        if self.enable_production:
            if not self.production_branch or not self.production_server or not self.production_server_path:
                raise ValidationError('Missed fields production_branch, production_server, production_server_path ')

        self.development_server_path = self.development_server_path.rstrip('/')
        self.production_server_path = self.production_server_path.rstrip('/')

        return super().clean_fields(exclude)

    def get_absolute_url(self):
        return self.repository_url

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
    email = models.EmailField(max_length=150, blank=False, unique=True)

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

    def generate_short_log(self):
        log = Logs.objects.filter(listener_id=self.listener.listener_uuid).order_by('datetime').reverse()[:20]
        text = ''
        for item in log:
            text += "({}) {} \n".format(item.datetime, item.message)
        return text

    def send_report(self, listener, subject, message):
        emails = listener.emails.all()
        recipients = []
        for item in emails:
            recipients.append(item.email)

        short_log = self.generate_short_log()
        message = "Hello! You have new events. \n\n\n {} \n\n Last 20 events: \n\n {}".format(message, short_log)

        try:
            send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)
        finally:
            pass

    def save_base(self, raw=False, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save_base(raw, force_insert, force_update, using, update_fields)
        if self.reported:
            self.send_report(self.listener,
                             "Deployer Report #{} of listener {}, {}".format(self.id, self.listener, self.datetime),
                             self.message)

    @classmethod
    def create_record(cls, listener, message, report=False):
        record = cls(listener=listener, message=message, reported=report)
        record.save()
        return record
