import os
import sys
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    name = "authentication"

    def ready(self):
        from . import signals
        if 'runserver' in sys.argv or os.environ.get('SERVER_SOFTWARE'):
            from . import scheduler
            scheduler.start()
