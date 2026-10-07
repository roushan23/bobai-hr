from django.apps import AppConfig


class BobaiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bobai"
    verbose_name = "BOBAI HR"

    def ready(self):
        from django.conf import settings
        from django.contrib import admin

        admin.site.site_header = settings.BRAND_NAME
        admin.site.site_title = settings.BRAND_NAME
        admin.site.index_title = "Administration"
