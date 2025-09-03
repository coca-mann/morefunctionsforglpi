from django.contrib import admin
from .models import Impressora, EtiquetaLayout

@admin.register(Impressora)
class ImpressoraAdmin(admin.ModelAdmin):
    # Adicionamos 'selecionada_para_impressao' na lista
    list_display = ('nome', 'localizacao', 'ativa', 'selecionada_para_impressao')
    list_filter = ('ativa', 'localizacao')
    search_fields = ('nome', 'localizacao')
    # Para facilitar a alteração rápida
    list_editable = ('ativa', 'selecionada_para_impressao')


@admin.register(EtiquetaLayout)
class EtiquetaLayoutAdmin(admin.ModelAdmin):
    list_display = ('nome', 'largura_mm', 'altura_mm', 'padrao')
    list_editable = ('padrao',)

