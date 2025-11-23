from django.urls import path
from . import views

urlpatterns = [
    path('glpi-sso/', views.glpi_sso, name='glpi_sso'),
]