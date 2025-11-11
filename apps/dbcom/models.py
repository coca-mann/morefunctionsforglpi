from django.db import models
# Se for usar criptografia para a senha, importe as bibliotecas aqui
from cryptography.fernet import Fernet
from django.conf import settings


class ExternalDbConfig(models.Model):
    """
    Armazena as credenciais de conexão para bancos de dados externos.
    """
    nome_conexao = models.CharField(
        max_length=100, 
        unique=True, 
        primary_key=True,
        help_text="Um nome único para esta conexão (ex: 'CRM_PRODUCAO')"
    )
    host = models.CharField(max_length=255)
    porta = models.PositiveIntegerField(default=3306)
    database = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    password = models.CharField(
        max_length=255,
    )

    # TODO: Implementar criptografia para o campo 'password'
    def save(self, *args, **kwargs):
        # Lógica para criptografar a senha antes de salvar
        cipher_suite = Fernet(settings.DB_ENCRYPTION_KEY)
        self.password = cipher_suite.encrypt(self.password.encode()).decode()
        super().save(*args, **kwargs)

    def get_decrypted_password(self):
        # Lógica para descriptografar ao ler
        cipher_suite = Fernet(settings.DB_ENCRYPTION_KEY)
        return cipher_suite.decrypt(self.password.encode()).decode()
        return self.password

    def __str__(self):
        return f"{self.nome_conexao} ({self.user}@{self.host})"

    class Meta:
        verbose_name = "Configuração de Banco Externo"
        verbose_name_plural = "Configurações de Bancos Externos"


class GLPIConfig(models.Model):
    """
    Armazena as configurações globais para a API v2 (OAuth2)
    e do fluxo de empréstimo. Implementa um padrão Singleton.
    """
    
    # --- Configurações da API v2 ---
    glpi_api_url = models.URLField(
        max_length=255, 
        default="https://glpi11.luffyslair.tec.br/api.php/v2",
        help_text="URL base da API v2 do GLPI."
    )
    # CAMPOS REMOVIDOS: glpi_app_token, glpi_user_token
    
    # CAMPOS NOVOS (OAuth2 Password Grant):
    glpi_client_id = models.CharField(
        max_length=255, 
        help_text="Client ID gerado em 'Configurar > Clientes OAuth'."
    )
    glpi_client_secret = models.CharField(
        max_length=255, 
        help_text="Client Secret gerado em 'Configurar > Clientes OAuth'."
    )
    glpi_api_username = models.CharField(
        max_length=100, 
        help_text="Nome de um usuário do GLPI com permissão de API."
    )
    glpi_api_password = models.CharField(
        max_length=100, 
        help_text="A senha do usuário de API."
    )
    
    # CAMPOS NOVOS (Cache do Token):
    glpi_access_token = models.TextField(
        blank=True, 
        null=True, 
        help_text="Token de acesso OAuth2 (gerenciado automaticamente)."
    )
    glpi_token_expires_at = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="Data/Hora de expiração do token (gerenciado automaticamente)."
    )

    # --- Configurações do Webhook ---
    webhook_secret_key = models.CharField(
        max_length=100, 
        help_text="Chave secreta para validar o payload do webhook."
    )
    
    # --- Configurações Específicas: Fluxo de Empréstimo ---
    status_emprestimo_id = models.PositiveIntegerField(
        default=5, 
        help_text="ID do Estado 'Em Empréstimo' (nos Ativos)."
    )
    status_operacional_id = models.PositiveIntegerField(
        default=2, 
        help_text="ID do Estado 'Operacional/Disponível' (nos Ativos)."
    )
    status_ticket_pendente_id = models.PositiveIntegerField(
        default=4, # <-- Baseado no seu log!
        help_text="ID do Status 'Pendente' (no Chamado) que dispara o empréstimo."
    )
    status_ticket_solucionado_id = models.PositiveIntegerField(
        default=5, # (Padrão comum do GLPI, verifique o seu)
        help_text="ID do Status 'Solucionado' (no Chamado) que dispara a devolução."
    )
    status_ticket_atendimento_id = models.PositiveIntegerField(
        default=2, # (Padrão comum do GLPI, verifique o seu)
        help_text="ID do Status 'Em atendimento' (no Chamado) que também dispara a devolução."
    )

    # ... (o resto do seu modelo Singleton, com save(), delete() e __str__()) ...
    def __str__(self):
        return "Configuração da Integração GLPI"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(GLPIConfig, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        pass # Não permite deletar

    class Meta:
        verbose_name = "Configuração da Integração GLPI"