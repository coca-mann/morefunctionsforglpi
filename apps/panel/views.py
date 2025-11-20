from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import DashboardSettings
from django.shortcuts import render
from django.http import JsonResponse
from apps.dbcom.glpi_queries import get_panel_data, tickets_resolved_today, tickets_open_today


def dashboard_page(request):
    """
    Renderiza a página HTML principal do painel.
    O template 'dbcom/dashboard.html' será criado a seguir.
    """
    return render(request, 'panel/dashboard.html')


def new_dashboard_page(request):
    """
    Renderiza a página HTML que irá carregar o novo painel em Vue.js.
    """
    return render(request, 'panel/new_dashboard.html')




def api_get_panel_data(request):
    """
    Uma view de API que retorna os dados do painel E OS CONTADORES em JSON.
    """

    try:
        data = get_panel_data()
        
        resolved_result = tickets_resolved_today()
        open_result = tickets_open_today()
        
        solved_count = 0
        if resolved_result:
            solved_count = resolved_result[0].get('Solved_today', 0)
        
        open_count = 0
        if open_result:
            open_count = open_result[0].get('Open_today', 0)
        
        response_data = {
            'data': data,
            'counters': {
                'resolved_today': solved_count,
                'open_today': open_count
            }
        }
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Erro na API ao buscar dados do GLPI: {e}")
        # Retorna um payload de erro consistente
        error_response = {
            'data': [],
            'counters': {'resolved_today': 0, 'open_today': 0},
            'error': str(e)
        }
        return JsonResponse(error_response, status=500)


@api_view(['GET']) # <-- ESTA LINHA É ESSENCIAL
@permission_classes([AllowAny])
def get_dashboard_settings(request):
    """
    Retorna o objeto de configurações do dashboard.
    Esta view é pública.
    """
    settings_obj = DashboardSettings.objects.get_settings()
    
    data = {
        'fetch_interval_seconds': settings_obj.fetch_interval_seconds,
        'notification_sound_url': settings_obj.notification_sound_url
    }
    
    return Response(data)
