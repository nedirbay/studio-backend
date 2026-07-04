import logging
import time

logger = logging.getLogger('api_requests')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log only API requests (path starting with /api) that are not GET requests
        is_api = request.path.startswith('/api/') or request.path.startswith('/api')
        is_logs_api = request.path.startswith('/api/admin/logs')
        if is_api and request.method != 'GET' and not is_logs_api:
            start_time = time.time()
            response = self.get_response(request)
            duration = time.time() - start_time
            
            user = request.user
            username = user.username if user and user.is_authenticated else 'Anonymous'
            
            logger.info(
                f"User: {username} | Method: {request.method} | Path: {request.path} | "
                f"Status: {response.status_code} | Duration: {duration:.3f}s"
            )
            return response
        
        return self.get_response(request)
