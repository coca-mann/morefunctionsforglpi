from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import admin, messages
from django.db.models import Count, Q
from .models import MotivoBaixa, LaudoBaixa, ItemLaudo, LaudoTecnico
from .forms import LaudoBaixaForm

# 1. Importe sua função de query do GLPI
#    Ajuste este 'import' para o caminho correto da sua função
try:
    from apps.dbcom.glpi_queries import get_equipamentos_para_baixa
    GLPI_IMPORT_DISPONIVEL = True
except ImportError:
    GLPI_IMPORT_DISPONIVEL = False
    print("AVISO: Função 'get_equipamentos_para_baixa' não encontrada.")
    print("A ação de importar do GLPI não funcionará.")


@admin.register(MotivoBaixa)
class MotivoBaixaAdmin(admin.ModelAdmin):
    """ Admin para os Motivos de Baixa. """
    list_display = ('codigo', 'titulo')
    search_fields = ('codigo', 'titulo', 'descricao')
    
    def has_module_permission(self, request):
        """ Esconde este modelo da página inicial do admin. """
        return False


class ItemLaudoInline(admin.TabularInline):
    """
    Define a visualização de 'Itens' dentro do admin do 'Laudo'.
    """
    model = ItemLaudo
    
    # Campos que aparecem no inline
    fields = (
        'nome_equipamento', 
        'tipo_equipamento', 
        'marca_equipamento', 
        'modelo_equipamento',
        'numero_patrimonio', 
        'numero_serie', 
        'motivo_baixa' # Este é o único campo editável!
    )
    
    # Campos que não podem ser editados pelo usuário no inline
    readonly_fields = (
        'nome_equipamento', 
        'tipo_equipamento', 
        'marca_equipamento', 
        'modelo_equipamento',
        'numero_patrimonio', 
        'numero_serie'
    )
    
    extra = 0 # Não mostrar formulários em branco por padrão
    can_delete = True # Permitir remover um item importado por engano
    
    def has_add_permission(self, request, obj):
        # Impede que o usuário adicione itens manualmente por este inline
        # Itens SÓ podem ser adicionados pela 'Admin Action'
        return False


@admin.register(LaudoBaixa)
class LaudoBaixaAdmin(admin.ModelAdmin):
    """ Admin principal para o Laudo de Baixa. """
    
    form = LaudoBaixaForm
    
    list_display = (
        'numero_documento', 
        'data_laudo', 
        'get_tecnico_nome_completo', 
        'destinacao', 
        'get_item_count',
        'link_imprimir_pdf'# Contagem de itens (método abaixo)
    )
    list_filter = ('data_laudo', 'tecnico_responsavel', 'destinacao')
    search_fields = ('numero_documento', 'tecnico_responsavel__username', 'itens__nome_equipamento')
    
    # Define os 'inlines'
    inlines = [ItemLaudoInline]
    
    # Ações customizadas
    actions = ['importar_itens_glpi']
    
    # Organização dos campos no formulário de edição
    fieldsets = (
        (None, {
            'fields': ('numero_documento', 'data_laudo', 'tecnico_responsavel')
        }),
        ('Destinação Final', {
            'fields': ('destinacao',)
        }),
    )
    
    # Torna o 'numero_documento' apenas leitura no formulário
    readonly_fields = ('numero_documento',)
    
    def get_queryset(self, request):
        """
        Sobrescreve o queryset principal para adicionar anotações
        que pré-calculam o status de cada laudo de uma só vez.
        """
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            # 1. Conta o total de itens
            _item_count=Count('itens', distinct=True),
            
            # 2. Conta quantos itens estão com o 'motivo_baixa' NULO (pendente)
            _missing_motivos=Count(
                'itens', 
                filter=Q(itens__motivo_baixa__isnull=True), 
                distinct=True
            )
        )
        return queryset
    
    @admin.display(
        description='Técnico Responsável', 
        ordering='tecnico_responsavel__first_name'
    )
    def get_tecnico_nome_completo(self, obj):
        # 'obj' é a instância do LaudoBaixa
        # Apenas chamamos a propriedade que já existe no models.py
        return obj.tecnico_nome_completo
    
    def link_imprimir_pdf(self, obj):
        """
        Verifica as condições antes de mostrar o link de impressão.
        Usa os valores pré-calculados do 'get_queryset'.
        """
        
        # 1. Verifica técnico
        if not obj.tecnico_responsavel:
            return "Pendente (Técnico)"

        # 2. Verifica destinação
        if not obj.destinacao:
            return "Pendente (Destinação)"
        
        # 3. Verifica se tem itens (usando a anotação)
        if obj._item_count == 0:
            return "Pendente (Sem itens)"
            
        # 4. Verifica se todos os itens têm motivo (usando a anotação)
        if obj._missing_motivos > 0:
            return f"Pendente ({obj._missing_motivos} itens sem motivo)"

        # Se todas as condições passarem:
        url = reverse('reports:gerar_pdf_laudo_baixa', args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Gerar PDF</a>')
    
    link_imprimir_pdf.short_description = "Imprimir Laudo"
    
    @admin.display(description='Qtd. Itens', ordering='_item_count')
    def get_item_count(self, obj):
        """
        Usa o valor pré-calculado '_item_count' do 'get_queryset'
        em vez de fazer uma nova query (obj.itens.count()).
        """
        return obj._item_count

    def get_actions(self, request):
        # Desabilita a ação de importação se a função não foi encontrada
        actions = super().get_actions(request)
        if not GLPI_IMPORT_DISPONIVEL:
            if 'importar_itens_glpi' in actions:
                del actions['importar_itens_glpi']
        return actions

    @admin.action(description='Importar equipamentos do GLPI para este laudo')
    def importar_itens_glpi(self, request, queryset):
        """
        Ação do Admin que busca dados no GLPI e cria os 'ItemLaudo'.
        """
        
        # 1. Validação: Ação só funciona para UM laudo de cada vez
        if queryset.count() != 1:
            self.message_user(request, 
                "Por favor, selecione apenas UM laudo para realizar a importação.", 
                messages.ERROR
            )
            return

        laudo = queryset.first()

        # 2. Executar a query do GLPI
        try:
            # Esta é a sua função!
            # Ela deve retornar uma LISTA de DICIONÁRIOS
            equipamentos_glpi = get_equipamentos_para_baixa() 
            
            if not equipamentos_glpi:
                self.message_user(request, "Nenhum equipamento encontrado no GLPI com o status de baixa.", messages.WARNING)
                return

        except Exception as e:
            self.message_user(request, f"Erro ao consultar o banco do GLPI: {e}", messages.ERROR)
            return

        # 3. Criar os objetos ItemLaudo
        itens_criados = 0
        itens_existentes = 0
        
        for equip in equipamentos_glpi:
            # 'equip' é o dicionário retornado pela sua query.
            # Ex: {'id': 123, 'nome': 'DELL-SN-12345', 'tipo': 'Computador', ...}
            # **Ajuste as chaves ('id', 'nome', etc.) para corresponder
            # ao que sua query retorna.**
            
            # get_or_create evita adicionar itens duplicados ao mesmo laudo
            obj, created = ItemLaudo.objects.get_or_create(
                laudo=laudo,
                glpi_id=equip['id'], # Chave 'id' do seu dicionário
                tipo_equipamento=equip['tipo'],
                defaults={
                    'nome_equipamento': equip['nome'],
                    'marca_equipamento': equip.get('marca', ''),
                    'modelo_equipamento': equip.get('modelo', ''),
                    'numero_patrimonio': equip.get('patrimonio', ''),
                    'numero_serie': equip.get('serie', '')
                }
            )
            
            if created:
                itens_criados += 1
            else:
                itens_existentes += 1
        
        # 4. Mensagem de sucesso
        msg = f"{itens_criados} novos itens importados para o laudo {laudo.numero_documento}. " \
              f"({itens_existentes} itens já constavam no laudo)."
        self.message_user(request, msg, messages.SUCCESS)

    def get_form(self, request, obj=None, **kwargs):
        # Coloca os campos na ordem desejada no formulário de edição
        self.fields = ('numero_documento', 'data_laudo', 'tecnico', 'destinacao_recomendada')
        return super().get_form(request, obj, **kwargs)
    
    def has_module_permission(self, request):
        """ Esconde este modelo da página inicial do admin. """
        return False


@admin.register(LaudoTecnico)
class LaudoTecnicoAdmin(admin.ModelAdmin):
    """
    Este admin 'falso' serve como o ponto de entrada no menu principal.
    Ele não tem lista de display, filtros, etc.
    Sua única função é redirecionar o usuário para a página de categorias.
    """
    
    def changelist_view(self, request, extra_context=None):
        """
        Sobrescreve a view de 'lista' (changelist) para redirecionar
        o usuário para a página de índice da sua app 'reports',
        onde está o seu template app_index.html customizado.
        """
        url = reverse('admin:app_list', kwargs={'app_label': self.model._meta.app_label})
        return HttpResponseRedirect(url)
            
    def has_module_permission(self, request):
        """ 
        Esta é a chave: esta função permite que o modelo
        seja exibido na página inicial do admin.
        """
        return True

