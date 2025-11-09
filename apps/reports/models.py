from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MotivoBaixa(models.Model):
    """
    Cadastra os motivos padronizados para a baixa de um equipamento.
    Ex: M1, M2, etc.
    """
    codigo = models.CharField(
        "Código", 
        max_length=10, 
        unique=True, 
        help_text="Ex: M1, M2"
    )
    titulo = models.CharField(
        "Título", 
        max_length=255
    )
    descricao = models.TextField(
        "Descrição Detalhada"
    )

    class Meta:
        verbose_name = "Motivo de Baixa"
        verbose_name_plural = "Motivos de Baixa"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo}: {self.titulo}"


class LaudoBaixa(models.Model):
    """
    O registro "pai" do Laudo Técnico de Baixa Patrimonial.
    Contém as informações gerais do documento.
    """
    DESTINACAO_CHOICES = [
        ('DESCARTE', 'Descarte Ecológico'),
        ('DOACAO', 'Doação'),
    ]

    numero_documento = models.CharField(
        "Nº do Documento",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Gerado automaticamente ao salvar. Ex: LT-2025-001"
    )
    data_laudo = models.DateField(
        "Data do Laudo",
        default=timezone.now,
        help_text="Data em que o laudo foi gerado."
    )
    tecnico_responsavel = models.ForeignKey(
        User,
        verbose_name="Técnico Responsável",
        on_delete=models.PROTECT,
        help_text="Usuário do Django que está emitindo o laudo."
    )
    destinacao = models.CharField(
        "Destinação Recomendada",
        max_length=10,
        choices=DESTINACAO_CHOICES,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Laudo de Baixa"
        verbose_name_plural = "Laudos de Baixa"
        ordering = ['-numero_documento']

    def __str__(self):
        if self.tecnico_responsavel:
            return f"{self.numero_documento} - {self.tecnico_responsavel.get_full_name()}"
        return self.numero_documento

    def save(self, *args, **kwargs):
        # Lógica para gerar o número do documento automático
        if not self.pk: # Apenas na criação (pk é None)
            ano_atual = timezone.now().year
            
            # 1. Busca o último laudo do ano atual
            ultimo_laudo = LaudoBaixa.objects.filter(
                numero_documento__startswith=f'LT-{ano_atual}'
            ).order_by('numero_documento').last()

            novo_numero_seq = 1
            if ultimo_laudo:
                # 2. Extrai o número sequencial (Ex: LT-2025-001 -> 001)
                try:
                    ultimo_seq_str = ultimo_laudo.numero_documento.split('-')[-1]
                    novo_numero_seq = int(ultimo_seq_str) + 1
                except (ValueError, IndexError):
                    pass # Mantém 1 se houver erro de formatação
            
            # 3. Formata o novo número
            # :03d garante 3 dígitos com zeros à esquerda (001, 002, ..., 010, ..., 100)
            self.numero_documento = f'LT-{ano_atual}-{novo_numero_seq:03d}'
            
        super().save(*args, **kwargs)


class ItemLaudo(models.Model):
    """
    Um equipamento ("item filho") associado a um Laudo de Baixa.
    Os dados do equipamento são copiados do GLPI.
    """
    laudo = models.ForeignKey(
        LaudoBaixa,
        verbose_name="Laudo",
        on_delete=models.CASCADE,
        related_name="itens" # Permite usar laudo.itens.all()
    )
    
    # --- Dados copiados do GLPI ---
    glpi_id = models.IntegerField(
        "ID GLPI", 
        editable=False
    )
    nome_equipamento = models.CharField(
        "Nome do Equipamento", 
        max_length=255, 
        editable=False
    )
    tipo_equipamento = models.CharField(
        "Tipo", 
        max_length=100, 
        editable=False
    )
    marca_equipamento = models.CharField(
        "Marca", 
        max_length=100, 
        null=True, 
        blank=True, 
        editable=False
    )
    modelo_equipamento = models.CharField(
        "Modelo", 
        max_length=100, 
        null=True, 
        blank=True, 
        editable=False
    )
    numero_patrimonio = models.CharField(
        "Nº Patrimônio", 
        max_length=50, 
        null=True, 
        blank=True, 
        editable=False
    )
    numero_serie = models.CharField(
        "Nº de Série", 
        max_length=100, 
        null=True, 
        blank=True, 
        editable=False
    )
    
    # --- Campo a ser preenchido pelo técnico no Django ---
    motivo_baixa = models.ForeignKey(
        MotivoBaixa,
        verbose_name="Motivo da Baixa",
        on_delete=models.SET_NULL,
        null=True,
        blank=False, # Força o usuário a escolher um motivo
        help_text="Selecione o motivo da baixa para este item."
    )

    class Meta:
        verbose_name = "Item do Laudo"
        verbose_name_plural = "Itens do Laudo"
        # Garante que um item do GLPI não seja adicionado duas vezes NO MESMO laudo
        unique_together = ('laudo', 'glpi_id', 'tipo_equipamento') 

    def __str__(self):
        return self.nome_equipamento
