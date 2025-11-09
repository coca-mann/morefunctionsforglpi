from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.adapter import get_adapter
from .views import GLPIOAuth2Adapter


class GLPIAccount(ProviderAccount):
    # Pode ser usado para adicionar helpers específicos do GLPI
    pass


class GLPIProvider(OAuth2Provider):
    id = 'glpi'
    name = 'GLPI'
    account_class = GLPIAccount
    
    oauth2_adapter_class = GLPIOAuth2Adapter

    def extract_uid(self, data):
        """
        Extrai o ID único do usuário da resposta da API do GLPI.
        
        IMPORTANTE: 'id' é um palpite. Você precisa verificar na documentação
        da API do GLPI qual campo contém o ID único do usuário.
        """
        return str(data['id'])

    def extract_common_fields(self, data):
        """
        Mapeia os dados da API do GLPI para os campos do modelo User do Django.
        
        IMPORTANTE: Os nomes 'email', 'username', 'first_name', 'last_name'
        são palpites. Verifique os nomes corretos na resposta da API do GLPI.
        """
        adapter = get_adapter()
        return adapter.populate_user_from_raw_data(
            data,
            mappings={
                "email": "email",
                "username": "username",
                "first_name": "first_name",
                "last_name": "last_name",
                "name": "name",
            },
        )._asdict()

    def get_default_scope(self):
        """
        Define os 'scopes' (permissões) que seu app pedirá ao GLPI.
        Ex: ['user:read', 'email:read']
        Verifique na documentação do GLPI quais scopes você precisa.
        """
        return ['user:read']