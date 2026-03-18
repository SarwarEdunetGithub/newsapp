from django.apps import AppConfig
import os

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):
        # Prevent scheduler from running multiple times in dev
        if os.environ.get('RUN_MAIN', None) != 'true':
            from . import tasks
            tasks.start()
