from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.contrib import admin
from .glpi_queries import get_assets_for_printing

@staff_member_required
def impressao_etiquetas_view(request):
    """
    Renderiza a página HTML personalizada para impressão de etiquetas.
    """
    
    # 2. PEGUE O CONTEXTO PADRÃO DO ADMIN
    # Isso inclui 'site_header', 'available_apps', etc.
    context = admin.site.each_context(request)
    
    # 3. DEFINA SEU CONTEÚDO CUSTOMIZADO
    tipos_de_ativos_display = [
        ('Computer', 'Computadores'),
        ('Monitor', 'Monitores'),
        ('Printer', 'Impressoras'),
        ('Phone', 'Telefones'),
        ('Networkequipment', 'Equip. de Rede'),
        ('Rack', 'Racks'),
        ('Consumableitem', 'Consumíveis'),
        ('Projetor', 'Projetores'),
        ('Scanner', 'Scanners'),
        ('Nobreak', 'Nobreaks'),
    ]

    # 4. ADICIONE SEU CONTEÚDO AO CONTEXTO PRINCIPAL
    context.update({
        'title': 'Impressão de Etiquetas de Ativos',
        'tipos_de_ativos_display': tipos_de_ativos_display,
        # 'opts' e 'app_label' não são mais necessários
        # pois o admin.site.each_context(request) já cuida disso.
    })
    
    # 5. RENDERIZE COM O CONTEXTO COMPLETO
    return render(request, 'admin/impressao_etiquetas.html', context)


#
# View 2: A API que busca os dados no GLPI (Sem mudanças)
#
@require_GET
@staff_member_required
def get_assets_data_api(request):
    """
    API interna que o JavaScript vai chamar para buscar os dados.
    """
    # ... (seu código desta view continua o mesmo)
    asset_type = request.GET.get('type')
    if not asset_type:
        return HttpResponseBadRequest("Parâmetro 'type' é obrigatório.")

    assets = get_assets_for_printing(asset_type)

    return JsonResponse(assets, safe=False)
