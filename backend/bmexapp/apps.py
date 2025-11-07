from django.apps import AppConfig


class MassesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bmexapp'
    verbose_name = 'Nuclear Masses'

    def ready(self):
        """Pre-load data cache on startup if using file mode."""
        # from django.conf import settings
        # if settings.BMEX_DATA_BACKEND == 'file':
        #     from .services.reference import DataLoader
        #     # Pre-warm the cache
        #     DataLoader.get_instance()
        pass
