import uuid
from django.db import models
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
    
    # --- Configurações da API v1 ---
    glpi_api_url = models.URLField(
        max_length=255, 
        default="https://glpi11.luffyslair.tec.br/api.php/v2",
        help_text="URL base da API v2 do GLPI."
    )
    glpi_app_token = models.CharField(
        max_length=100, 
        help_text="Token de Aplicação (App-Token) gerado em 'Configurar > Geral > API'."
    )
    glpi_user_token = models.CharField(
        max_length=100, 
        help_text="Token Pessoal de Acesso (User-Token) de um usuário com permissão."
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


class GLPIWebhook(models.Model):
    """
    Cadastra um Webhook do GLPI. Gera uma URL única para
    receber as chamadas e agrupar regras de automação.
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="ID único que será usado na URL do webhook."
    )
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nome descritivo (ex: Automação de Chamados de TI)."
    )
    secret_key = models.CharField(
        max_length=100, 
        help_text="Segredo do Webhook (definido no GLPI) para validação (atualmente ignorado).",
        blank=True
    )
    
    def get_url(self):
        
        if not self.pk:
            return "A URL será gerada e exibida aqui após salvar."

        base = settings.BASE_URL.rstrip('/') 
        return f"{base}/api/glpi/webhook/{self.id}/"
    get_url.short_description = "URL para o GLPI"

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Webhook do GLPI"
        verbose_name_plural = "Webhooks do GLPI"


class AutomationRule(models.Model):
    """
    Define uma regra de automação baseada na Categoria ITIL
    e vinculada a um Webhook específico.
    """
    webhook = models.ForeignKey(
        GLPIWebhook, 
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="O Webhook que acionará esta regra.",
        null=True,  # <-- CONFIRME QUE ISSO ESTÁ AQUI
        blank=True  # <-- CONFIRME QUE ISSO ESTÁ AQUI
    )
    name = models.CharField(
        'Nome',
        max_length=100,
        help_text="Nome descritivo da regra (ex: Reparo de Monitor)."
    )
    trigger_category_id = models.PositiveIntegerField(
        "ID da Categoria (Gatilho)",
        help_text="ID da Categoria ITIL (ou Categoria PAI) que dispara esta regra."
    )
    
    # --- IDs dos Status do CHAMADO ---
    trigger_pending_id = models.PositiveIntegerField(
        "ID do Status 'Pendente' do Chamado",
        help_text="ID do Status 'Pendente' (no Chamado) que inicia a ação."
    )
    trigger_solve_ids = models.CharField(
        "IDs dos Status 'Solucionado' do Chamado",
        max_length=50, 
        default="5",
        help_text="IDs dos Status (separados por vírgula, ex: 5,2) que revertem a ação.",
    )
    
    # --- IDs dos Status do ATIVO ---
    target_asset_status_on_pending = models.PositiveIntegerField(
        "ID do Status do Ativo (Pendente)",
        help_text="ID do Status do Ativo para definir quando 'Pendente' (ex: Em Manutenção)."
    )
    target_asset_status_on_solve = models.PositiveIntegerField(
        "ID do Status do Ativo (Solucionado)",
        help_text="ID do Status do Ativo para definir quando 'Solucionado' (ex: Operacional)."
    )
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        # Garante que uma categoria só tenha uma regra por webhook
        unique_together = ('webhook', 'trigger_category_id')
        verbose_name = "Regra de Automação"
        verbose_name_plural = "Regras de Automação"