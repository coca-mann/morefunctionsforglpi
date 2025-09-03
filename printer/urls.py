from django.urls import path
from . import views

urlpatterns = [
    # Endpoints de Impressoras
    path('impressoras/', views.listar_impressoras_api, name='api_listar_impressoras'),
    path('impressoras/<int:pk>/selecionar-padrao/', views.selecionar_impressora_padrao_api, name='api_selecionar_impressora'),

    # Endpoints de Layouts
    path('layouts/', views.listar_layouts_api, name='api_listar_layouts'),
    path('layouts/<int:pk>/', views.detalhe_layout_api, name='api_detalhe_layout'),
    path('layouts/<int:pk>/selecionar-padrao/', views.selecionar_layout_padrao_api, name='api_selecionar_layout'),

    # Endpoint de Impressão
    path('imprimir/', views.imprimir_etiquetas_api, name='api_imprimir'),
]