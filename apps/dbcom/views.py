from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.contrib import admin
from .glpi_queries import get_panel_data, get_assets_for_printing
import datetime

def dashboard_page(request):
    """
    Renderiza a página HTML principal do painel.
    O template 'dbcom/dashboard.html' será criado a seguir.
    """
    return render(request, 'dbcom/dashboard.html')


def api_get_panel_data(request):
    """
    Uma view de API que retorna os dados do painel em formato JSON.
    Esta view será chamada a cada 30 segundos pelo JavaScript.
    
    Como a query 'get_panel_data' já traz os dados formatados,
    esta view apenas busca os dados e os retorna.
    """
    try:
        data = get_panel_data()
    except Exception as e:
        # Captura erros da query (ex: conexão falhou)
        print(f"Erro na API ao buscar dados do GLPI: {e}")
        return JsonResponse({'data': [], 'error': str(e)}, status=500)
        
    return JsonResponse({'data': data})


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
    
    data_for_frontend = [
        {"titulo": item['asset_name'], "url": item['url']}
        for item in assets
    ]

    return JsonResponse(data_for_frontend, safe=False)