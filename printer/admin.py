from django.contrib import admin
from .models import Impressora, EtiquetaLayout

@admin.register(Impressora)
class ImpressoraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'localizacao', 'porta', 'ativa', 'selecionada_para_impressao')
    list_filter = ('ativa', 'selecionada_para_impressao', 'localizacao')
    search_fields = ('nome', 'localizacao', 'driver', 'porta')
    actions = ['marcar_como_padrao']

    def marcar_como_padrao(self, request, queryset):
        # Apenas uma pode ser padrão, então pegamos a primeira da seleção
        if queryset.exists():
            impressora = queryset.first()
            impressora.selecionada_para_impressao = True
            impressora.save() # Nosso save() cuida do resto
            self.message_user(request, f"Impressora '{impressora.nome}' definida como padrão.")
    marcar_como_padrao.short_description = "Marcar selecionada como padrão"


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