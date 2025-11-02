# seu_projeto/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from printer.views import rodar_sincronizacao_impressoras
from apps.dbcom import views as dbcom_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/sincronizar-impressoras/', rodar_sincronizacao_impressoras, name='sincronizar_impressoras'),
    path('admin/impressao-etiquetas/', dbcom_views.impressao_etiquetas_view, name='admin_impressao_etiquetas'),
    path('api/get-assets/', dbcom_views.get_assets_data_api, name='api_get_assets'),
    path('admin/', admin.site.urls),
    path('glpi/', include('apps.panel.urls')),
    path('api/', include('printer.urls')),
    # URLs de autenticação JWT
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
