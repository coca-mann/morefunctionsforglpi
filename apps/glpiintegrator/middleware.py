class AllowAdminInIframeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        admin_path = '/admin/'
        
        if request.path.startswith(admin_path):
            if response.has_header('X-Frame-Options'):
                response.delete_header('X-Frame-Options')
        
        return response
