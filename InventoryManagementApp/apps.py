from django.apps import AppConfig


class InventorymanagementappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'InventoryManagementApp'

    def ready(self):
        import InventoryManagementApp.signals  # noqa

