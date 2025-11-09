from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import GLPIProvider

urlpatterns = default_urlpatterns(GLPIProvider)