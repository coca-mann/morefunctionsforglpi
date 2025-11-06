from django.urls import path
from . import views

urlpatterns = [
    # Endpoints de Layouts
    path('layouts/', views.listar_layouts_api, name='api_listar_layouts'),
    path('layouts/<int:pk>/', views.detalhe_layout_api, name='api_detalhe_layout'),
    path('layouts/<int:pk>/selecionar-padrao/', views.selecionar_layout_padrao_api, name='api_selecionar_layout'),

    # Endpoint de Impressão
    path('imprimir/', views.imprimir_etiquetas_api, name='api_imprimir'),
    path('api/print_server/<int:pk>/test/', views.test_print_server_connection, name='api_test_print_server'),
    path('api/print_server/<int:pk>/fetch/', views.fetch_remote_printers, name='api_fetch_remote_printers'),
]