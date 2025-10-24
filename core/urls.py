# seu_projeto/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from printer.views import rodar_sincronizacao_impressoras

urlpatterns = [
    path('admin/sincronizar-impressoras/', rodar_sincronizacao_impressoras, name='sincronizar_impressoras'),
    path('admin/', admin.site.urls),
    path('api/', include('printer.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
