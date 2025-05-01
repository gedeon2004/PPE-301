from django.apps import AppConfig


class BoutiqueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'boutique'

    def ready(self):
        import boutique.templatetags.custom_filters  # Active les tags