from django.contrib import admin
from .models import EtiquetaLayout, PrintServer
from .forms import PrintServerAdminForm


@admin.register(PrintServer)
class PrintServerAdmin(admin.ModelAdmin):
    """
    Admin para o novo modelo de Servidor de Impressão.
    """
    list_display = ('nome', 'endereco_servico', 'nome_impressora_padrao', 'ativo', 'atualizado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'endereco_servico', 'nome_impressora_padrao')
    
    form = PrintServerAdminForm
    
    # Organiza os campos no admin
    fieldsets = (
        (None, {
            'fields': ('nome', 'ativo')
        }),
        ('Detalhes da Conexão', {
            'fields': ('endereco_servico', 'api_key_input'),
            'description': 'Informações para conectar ao serviço de impressão do Windows.'
        }),
        ('Configuração da Impressora', {
            'fields': ('nome_impressora_padrao',),
            'description': 'Clique nos botões (que aparecerão abaixo após salvar) para buscar e definir a impressora.'
        }),
    )
    
    # 1. Aponta para um template customizado (onde colocaremos os botões)
    change_form_template = 'admin/printer/printserver/change_form.html'
    
    # 2. Injeta o JavaScript customizado nesta página
    class Media:
        js = (
            'admin/js/jquery.init.js', # Garante que o jQuery do admin esteja carregado
            'printer/js/print_server_admin.js', # Nosso novo JS para os botões
        )
        css = {
            'all': ('printer/css/print_server_admin.css',)
        }


@admin.register(EtiquetaLayout)
class EtiquetaLayoutAdmin(admin.ModelAdmin):
    list_display = ('nome', 'largura_mm', 'altura_mm', 'padrao', 'atualizado_em')
    list_filter = ('padrao',)
    search_fields = ('nome', 'descricao')
    
    # 1. Template do editor (Sem mudança)
    change_form_template = 'admin/printer/etiquetalayout/change_form.html'
    
    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/interactjs/dist/interact.min.js', 
            'printer/js/layout_editor.js',
        )
        css = {
            'all': ('printer/css/layout_editor.css',),
        }