from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError



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
    
    @property
    def tecnico_nome_completo(self):
        """ Retorna o nome completo do usuário do Django. """
        if self.tecnico_responsavel:
            return self.tecnico_responsavel.get_full_name()
        return "N/A"

    @property
    def get_destinacao_recomendada_display(self):
        """ Propriedade para o template de PDF usar o nome legível. """
        return self.get_destinacao_display()


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


class LaudoTecnico(LaudoBaixa):
    """
    Modelo Proxy usado para criar um 'atalho' no menu principal do admin.
    Ele não cria uma nova tabela no banco de dados.
    """
    class Meta:
        # Informa ao Django que este é um modelo proxy
        proxy = True 
        
        # Este é o nome que aparecerá no menu do admin
        verbose_name = "Laudo Técnico para Baixa Patrimonial"
        verbose_name_plural = "Laudos Técnicos para Baixa Patrimonial"


class ProtocoloReparo(models.Model):
    """
    O registro "pai" do Protocolo de Envio para Reparo.
    """
    numero_documento = models.CharField(
        "Nº do Documento",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Gerado automaticamente ao salvar. Ex: PRE-2025-001"
    )
    data_protocolo = models.DateField(
        "Data do Protocolo",
        default=timezone.now
    )
    tecnico_responsavel = models.ForeignKey(
        User,
        verbose_name="Técnico Responsável",
        on_delete=models.PROTECT
    )
    # Vamos salvar o ID e o Nome do Fornecedor (vindo do GLPI)
    glpi_fornecedor_id = models.IntegerField(
        "ID Fornecedor GLPI",
        null=True, blank=False # Não pode ser nulo após selecionado
    )
    glpi_fornecedor_nome = models.CharField(
        "Nome do Fornecedor",
        max_length=255,
        null=True, blank=False
    )

    class Meta:
        verbose_name = "Protocolo de Reparo"
        verbose_name_plural = "Protocolos de Reparo"
        ordering = ['-numero_documento']

    def __str__(self):
        return f"{self.numero_documento} - {self.glpi_fornecedor_nome or 'N/A'}"

    def save(self, *args, **kwargs):
        # Lógica para gerar o número do documento automático
        if not self.pk:
            ano_atual = timezone.now().year
            prefixo = 'PRE'
            
            ultimo_protocolo = ProtocoloReparo.objects.filter(
                numero_documento__startswith=f'{prefixo}-{ano_atual}'
            ).order_by('numero_documento').last()

            novo_numero_seq = 1
            if ultimo_protocolo:
                try:
                    ultimo_seq_str = ultimo_protocolo.numero_documento.split('-')[-1]
                    novo_numero_seq = int(ultimo_seq_str) + 1
                except (ValueError, IndexError):
                    pass
            
            self.numero_documento = f'{prefixo}-{ano_atual}-{novo_numero_seq:03d}'
        
        super().save(*args, **kwargs)

    @property
    def tecnico_nome_completo(self):
        """ Retorna o nome completo do usuário do Django. """
        if self.tecnico_responsavel:
            return self.tecnico_responsavel.get_full_name()
        return "N/A"


class ItemReparo(models.Model):
    """
    Um equipamento ("item filho") associado a um Protocolo de Reparo.
    Os dados são copiados do GLPI (Ticket + Item).
    """
    protocolo = models.ForeignKey(
        ProtocoloReparo,
        verbose_name="Protocolo",
        on_delete=models.CASCADE,
        related_name="itens"
    )
    
    # --- Dados copiados do GLPI ---
    glpi_ticket_id = models.IntegerField("ID Ticket GLPI")
    glpi_item_id = models.IntegerField("ID Item GLPI")
    glpi_item_tipo = models.CharField("Tipo Item GLPI", max_length=255)
    
    nome_item = models.CharField("Nome do Equipamento", max_length=255)
    numero_serie = models.CharField("Nº de Série", max_length=100, null=True, blank=True)
    numero_patrimonio = models.CharField("Nº Patrimônio", max_length=50, null=True, blank=True)
    
    titulo_ticket = models.TextField("Título do Chamado", null=True, blank=True)
    observacao_ticket = models.TextField("Observação do Chamado", null=True, blank=True)

    class Meta:
        verbose_name = "Item de Reparo"
        verbose_name_plural = "Itens de Reparo"
        # Garante que um item de um ticket não seja adicionado duas vezes
        # NO MESMO protocolo
        unique_together = ('protocolo', 'glpi_ticket_id', 'glpi_item_id')

    def __str__(self):
        return self.nome_item

    @property
    def tipo_equipamento_formatado(self):
        """ 
        Formata o tipo de item para ser legível.
        Ex: "Glpi\CustomAsset\nobreakAsset" -> "Nobreak"
        """
        if self.glpi_item_tipo:
            return self.glpi_item_tipo.split('\\')[-1].replace('Asset', '').upper()
        return 'N/A'


class ProtocoloReparoProxy(ProtocoloReparo):
    """
    Modelo Proxy usado para criar um 'atalho' no menu principal do admin
    para o módulo de Protocolos de Reparo.
    """
    class Meta:
        proxy = True
        verbose_name = "Protocolo de Envio para Reparo"
        verbose_name_plural = "Protocolos de Envio para Reparo"


class ConfiguracaoCabecalho(models.Model):
    """
    Modelo Singleton para armazenar os dados da empresa
    que aparecem nos cabeçalhos dos relatórios.
    """
    logo = models.ImageField(
        "Logo da Empresa",
        upload_to='logos/',
        null=True, blank=False,
        help_text="Faça upload da imagem da logo (ex: .png, .jpg)"
    )
    nome_fantasia = models.CharField(
        "Nome Fantasia", 
        max_length=255
    )
    cnpj = models.CharField(
        "CNPJ", 
        max_length=18, # Formato: 00.000.000/0001-00
        help_text="Ex: 00.000.000/0001-00"
    )
    endereco_completo = models.CharField(
        "Endereço Completo", 
        max_length=500,
        help_text="Ex: Rua Exemplo, 123, Bairro, Cidade - UF, CEP 00000-000"
    )

    class Meta:
        verbose_name = "Configuração do Cabeçalho"
        verbose_name_plural = "Configurações do Cabeçalho"

    def __str__(self):
        return f"Configuração do Cabeçalho ({self.nome_fantasia})"

    def save(self, *args, **kwargs):
        """
        Garante que apenas um objeto ConfiguracaoCabecalho exista.
        (Padrão Singleton)
        """
        if not self.pk and ConfiguracaoCabecalho.objects.exists():
            raise ValidationError(
                'Só pode haver uma instância de Configuração de Cabeçalho. '
                'Edite a existente em vez de criar uma nova.'
            )
        return super(ConfiguracaoCabecalho, self).save(*args, **kwargs)


