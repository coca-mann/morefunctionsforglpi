from django.db import models
from django.db.models import JSONField

class Impressora(models.Model):
    # O nome principal, que usaremos como identificador único
    nome = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Nome da impressora como aparece no Windows (pPrinterName)."
    )
    # Campos para armazenar os dados capturados
    driver = models.CharField(max_length=255, blank=True, help_text="Nome do driver (pDriverName).")
    porta = models.CharField(max_length=100, blank=True, help_text="Porta de conexão (pPortName).")
    localizacao = models.CharField(max_length=255, blank=True, null=True, help_text="Localização física (pLocation).")
    comentario = models.TextField(blank=True, null=True, help_text="Comentários da impressora (pComment).")
    
    # Códigos numéricos brutos do sistema
    status_code = models.IntegerField(null=True, blank=True, help_text="Código de status numérico do Windows (Status).")
    attributes_code = models.IntegerField(null=True, blank=True, help_text="Código de atributos numérico (Attributes).")

    # Nosso controle interno
    ativa = models.BooleanField(
        default=True,
        help_text="Controle interno para habilitar ou desabilitar o uso desta impressora no sistema."
    )
    selecionada_para_impressao = models.BooleanField(
        default=False,
        help_text="Marque esta opção para definir esta como a impressora padrão do sistema."
    )
    
    # Datas de sincronização
    ultima_sincronizacao = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que apenas uma impressora
        seja a selecionada para impressão.
        """
        # Se este objeto está sendo marcado como o selecionado
        if self.selecionada_para_impressao:
            # Desmarca todas as outras impressoras. O .exclude(pk=self.pk) garante
            # que não desmarquemos o objeto que estamos prestes a salvar.
            Impressora.objects.filter(selecionada_para_impressao=True).exclude(pk=self.pk).update(selecionada_para_impressao=False)
        
        super(Impressora, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Impressora"
        verbose_name_plural = "Impressoras"


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