from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path(
        'laudo/<int:laudo_id>/pdf/',
        views.gerar_pdf_laudo_baixa,
        name='gerar_pdf_laudo_baixa'
    ),
]