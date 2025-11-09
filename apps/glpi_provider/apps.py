from django.apps import AppConfig


class GlpiProviderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.glpi_provider'
    
    def ready(self):
        # Importações devem ser feitas DENTRO do método
        # para evitar o AppRegistryNotReady
        import allauth.socialaccount.providers
        from .provider import GLPIProvider  # Use import relativo

        allauth.socialaccount.providers.registry.register(GLPIProvider)