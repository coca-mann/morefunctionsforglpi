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
