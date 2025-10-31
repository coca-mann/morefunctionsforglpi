from django.shortcuts import render
from django.http import JsonResponse
from .glpi_queries import get_panel_data
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
