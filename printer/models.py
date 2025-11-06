import os
from django.db import models
from django.db.models import JSONField
from dotenv import load_dotenv
from cryptography.fernet import Fernet


load_dotenv()

try:
    fern_obj = Fernet(os.getenv('DB_ENCRYPTION_KEY'))
except Exception as e:
    print(f"AVISO CRÍTICO: Não foi possível carregar a FERNET_KEY das configurações. {e}")
    fern_obj = None


class PrintServer(models.Model):
    """
    Armazena os detalhes de conexão de um serviço de impressão remoto.
    Substitui o antigo modelo 'Impressora'.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        help_text="Um nome amigável para este servidor (ex: 'Zebra da Expedição', 'Impressora da TI')."
    )
    endereco_servico = models.CharField(
        max_length=255,
        help_text="Endereço IP e porta do serviço de impressão. Ex: http://192.168.1.50:5001"
    )
    api_key = models.TextField(
        blank=True,
        help_text="A chave 'X-API-Key' secreta (será salva criptografada).",
        verbose_name="Chave de API (Criptografada)"
    )
    nome_impressora_padrao = models.CharField(
        max_length=255,
        blank=True,
        help_text="O nome exato da impressora no Windows a ser usada por este serviço (ex: 'Zebra ZD420').",
        verbose_name="Impressora Padrão"
    )
    ativo = models.BooleanField(
        default=False,
        help_text="Define este como o servidor de impressão ativo para todas as impressões do sistema."
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        """ Garante que apenas um servidor de impressão possa ser 'ativo'. """
        if self.ativo:
            PrintServer.objects.filter(ativo=True).exclude(pk=self.pk).update(ativo=False)
        
        # A lógica de criptografia será movida para o 'forms.py'
        # para lidar corretamente com a entrada do admin.
        super(PrintServer, self).save(*args, **kwargs)

    # --- NOVO: Métodos de Criptografia ---
    def set_api_key(self, plain_key: str):
        """
        Criptografa uma chave de texto simples e a armazena.
        """
        if not fern_obj:
            raise ValueError("FERNET_KEY não está configurada.")
        if not plain_key:
            self.api_key = ""
        else:
            encrypted_key = fern_obj.encrypt(plain_key.encode('utf-8'))
            self.api_key = encrypted_key.decode('utf-8')

    def get_decrypted_api_key(self) -> str:
        """
        Descriptografa a chave armazenada e a retorna como texto simples.
        """
        if not fern_obj:
            raise ValueError("FERNET_KEY não está configurada.")
        if not self.api_key:
            return ""
        
        try:
            decrypted_key = fern_obj.decrypt(self.api_key.encode('utf-8'))
            return decrypted_key.decode('utf-8')
        except Exception as e:
            print(f"Erro ao descriptografar a chave para PrintServer {self.id}: {e}")
            return "" # Retorna vazio em caso de falha

    class Meta:
        verbose_name = "Servidor de Impressão"
        verbose_name_plural = "Servidores de Impressão"


class EtiquetaLayout(models.Model):
    """
    Armazena as configurações de design para um tipo de etiqueta.
    AGORA COM SUPORTE A LAYOUT DINÂMICO.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome descritivo do layout, ex: 'Etiqueta Padrão Patrimônio 50x50mm'"
    )
    descricao = models.TextField(blank=True, help_text="Descrição opcional do uso deste layout.")
    
    # --- DIMENSÕES (Sem mudança) ---
    largura_mm = models.FloatField(default=50, help_text="Largura da etiqueta em milímetros (mm).")
    altura_mm = models.FloatField(default=50, help_text="Altura da etiqueta em milímetros (mm).")
    
    # --- FONTE (Sem mudança) ---
    # (Mantemos isso pois a fonte é uma propriedade do layout, não de um elemento)
    arquivo_fonte = models.FileField(
        upload_to='fonts/',
        help_text="Arquivo da fonte .ttf (ex: ariblk.ttf). Faça o upload aqui."
    )
    nome_fonte_reportlab = models.CharField(
        max_length=50,
        help_text="Nome a ser usado para registrar a fonte no ReportLab (ex: 'Arial-Black')."
    )

    # --- CAMPO DINÂMICO (A GRANDE MUDANÇA) ---
    # Este campo vai armazenar a "receita" do layout (posições, tamanhos, etc.)
    layout_json = JSONField(
        default=list, # Por padrão, é uma lista vazia
        blank=True,
        help_text="Definição JSON dos elementos do layout (gerenciado pelo editor visual)."
    )

    # --- CAMPOS ANTIGOS (REMOVIDOS) ---
    # altura_titulo_mm (agora vive dentro do layout_json)
    # tamanho_fonte_titulo (agora vive dentro do layout_json)
    # margem_vertical_qr_mm (agora vive dentro do layout_json)

    # --- CONTROLE (Sem mudança) ---
    padrao = models.BooleanField(
        default=False,
        help_text="Marque para definir este como o layout padrão para novas impressões."
    )
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        """ Garante que apenas um layout seja o padrão. """
        if self.padrao:
            EtiquetaLayout.objects.filter(padrao=True).exclude(pk=self.pk).update(padrao=False)
        super(EtiquetaLayout, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Layout de Etiqueta"
        verbose_name_plural = "Layouts de Etiqueta"