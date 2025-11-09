from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib import admin, messages
from .models import MotivoBaixa, LaudoBaixa, ItemLaudo

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
    
    list_display = (
        'numero_documento', 
        'data_laudo', 
        'tecnico_responsavel', 
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
    
    def link_imprimir_pdf(self, obj):
        # 'obj' é a instância do LaudoBaixa
        if obj.pk: # Se o laudo já foi salvo
            # 'reports:gerar_pdf_laudo_baixa' vem do urls.py (app_name:name)
            url = reverse('reports:gerar_pdf_laudo_baixa', args=[obj.pk])
            return mark_safe(f'<a href="{url}" target="_blank">Gerar PDF</a>')
        return "N/A (salve primeiro)"
    link_imprimir_pdf.short_description = "Imprimir Laudo"
    
    @admin.display(description='Qtd. Itens')
    def get_item_count(self, obj):
        return obj.itens.count()

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
