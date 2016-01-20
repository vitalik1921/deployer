import os
import json
from django.core.exceptions import ImproperlyConfigured


def get_secret(setting, base_dir):
    """Get secrets from JSON file"""

    with open(os.path.join(base_dir, "settings", "secrets.json")) as secrets_file:
        content = secrets_file.read()
        secrets = json.loads(content)

    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {0} environment variable".format(setting)
        raise ImproperlyConfigured(error_msg)
