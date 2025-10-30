from django.db import models

class Configuration(models.Model):
    
    client_id = models.CharField(
        null=True, blank=True,
        help_text='Client ID gerado para o Cliente OAuth no GLPI'
    )
    client_secret = models.CharField(
        null=True, blank=True,
        help_text='Client Secret gerado para o cliente OAuth no GLPI'
    )
    username = models.CharField(
        null=True, blank=True,
        help_text='Usuário para autenticação no GLPI'
    )
    password = models.CharField(
        null=True, blank=True,
        help_text='Usuário para autenticação no GLPI'
    )
    grant_type = models.CharField(
        default='password',
        help_text='Tipo de autenticação'
    )
    token_type = models.CharField(
        null=True, blank=True,
        help_text='Tipo de token obtido na requisição de autenticação'
    )
    expires_in = models.CharField(
        null=True, blank=True,
        help_text='Tempo para expirar o token'
    )
    access_token = models.CharField(
        null=True, blank=True,
        help_text='Token de acesso utilizado nas requisições'
    )
    refresh_token = models.CharField(
        null=True, blank=True,
        help_text='Token de atualização para quando o token de acesso expirar'
    )
