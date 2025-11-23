class AllowAdminInIframeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        
        admin_path = '/admin/'
        
        if not request.path.startswith(admin_path):
            response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
