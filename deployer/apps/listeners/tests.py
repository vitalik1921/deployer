import json

from django.test import TestCase
from django.test import Client


class ListenersEvents(TestCase):
    def setUp(self):
        self.client = Client()

    def test_webhook_request(self):
        webhook = json.dumps({
            "actor": "User",
            "repository": "Repository",
            "push": {
             "links": "aaa"
            }
        })
        response = self.client.post('/webhook/test_slug', data=webhook, content_type='application/json')
        self.assertContains(response=response, text="User", count=1)

