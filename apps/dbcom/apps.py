from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class DbcomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dbcom'

    def ready(self):
        """
        Sempre que o usuário fizer login (Admin ou App), 
        sincronizamos os perfis do GLPI com os grupos do Django.
        """
        from .utils import sync_glpi_user_groups
        
        def on_user_logged_in(sender, request, user, **kwargs):
            # Se o usuário não for do sistema (ex: superuser manual), 
            # podemos querer ignorar, mas para sua lógica, sincronizamos todos.
            try:
                print(f"[AUTH] Usuário '{user.username}' logado. Iniciando sincronização GLPI...")
                sync_glpi_user_groups(user)
            except Exception as e:
                print(f"[AUTH] Falha crítica na sincronização de perfis: {e}")

        # Conecta o sinal de login à nossa função de sincronização
        user_logged_in.connect(on_user_logged_in)
