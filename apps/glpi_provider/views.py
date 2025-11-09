from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

class GLPIOAuth2Adapter(OAuth2Adapter):
    provider_id = 'glpi' # Correto, como fizemos antes

    # --- INÍCIO DA CORREÇÃO ---
    # Substitua as URLs antigas por estas:

    # 1. Endpoint de Autorização (A página HTML onde o usuário faz login)
    authorize_url = 'https://glpi11.luffyslair.tec.br/api.php/oauth2/authorize'
    
    # 2. Endpoint de Token (Onde o Django troca o 'código' pelo 'token')
    access_token_url = 'https://glpi11.luffyslair.tec.br/api.php/oauth2/token'
    
    # 3. Endpoint de Perfil (Onde o Django busca os dados do usuário)
    profile_url = 'https://glpi11.luffyslair.tec.br/api.php/v2/user/me'
    
    # --- FIM DA CORREÇÃO ---

    access_token_method = 'POST'
    access_token_type = 'Bearer'

# Expõe as views para o allauth
oauth2_login = OAuth2LoginView.adapter_view(GLPIOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(GLPIOAuth2Adapter)