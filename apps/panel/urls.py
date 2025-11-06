from django.urls import path
from apps.panel import views

urlpatterns = [
    # Rota para a página principal (HTML)
    path('painel/', views.dashboard_page, name='painel_dashboard'),
    
    # Rota para a API de dados (JSON)
    path('api/dados-painel/', views.api_get_panel_data, name='api_painel_data'),
    path('api/dashboard/settings/', views.get_dashboard_settings, name='api_get_dashboard_settings'),
]
