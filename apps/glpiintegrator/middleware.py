from django.conf import settings

class AllowAdminInIframeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Permitir que as origens configuradas incorporem o Django
        # frame-ancestors substitui o X-Frame-Options nos navegadores modernos
        csp_policy = f"frame-ancestors {settings.CSP_FRAME_ANCESTORS}"
        response['Content-Security-Policy'] = csp_policy
        
        # Remover X-Frame-Options para que o Content-Security-Policy prevaleça
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
            
        return response
