import os
import django
import json
import inspect
from django.conf import settings
from django.urls import URLPattern, URLResolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from config.urls import urlpatterns

def get_urls(patterns, prefix=''):
    endpoints = []
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            route = prefix + str(pattern.pattern)
            
            # Simple route cleanup
            route = route.replace('^', '').replace('$', '').replace('\\/', '/')
            
            # Get allowed methods if view is a class-based view or DRF view
            methods = []
            callback = pattern.callback
            if hasattr(callback, 'view_class'):
                view_class = callback.view_class
                if hasattr(view_class, 'http_method_names'):
                    methods = [m.upper() for m in view_class.http_method_names if m.upper() != 'OPTIONS']
            elif hasattr(callback, 'cls'):
                # DRF ViewSet actions
                if hasattr(callback, 'actions') and callback.actions:
                    methods = [m.upper() for m in callback.actions.keys() if m.upper() != 'OPTIONS']
            
            if not methods:
                methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']  # Fallback

            # Try to get the file where the handler is defined
            file_path = "Unknown"
            try:
                module = inspect.getmodule(pattern.callback)
                if module:
                    file_path = module.__file__
            except Exception:
                pass
                
            handler_name = pattern.name or getattr(pattern.callback, '__name__', 'Unknown')
            
            for method in methods:
                endpoints.append({
                    "method": method,
                    "path": f"/{route}" if not route.startswith('/') else route,
                    "file": file_path,
                    "handler": handler_name,
                    "authentication_required": True, # Approximated for this project
                })
                
        elif isinstance(pattern, URLResolver):
            new_prefix = prefix + str(pattern.pattern)
            endpoints.extend(get_urls(pattern.url_patterns, new_prefix))
            
    return endpoints

endpoints = get_urls(urlpatterns)

inventory = {
    "endpoints": endpoints,
    "models": ["User", "AuditLog", "ReportingPeriod", "Report", "Comment", "Notification"],
    "services": [],
    "auth": {"type": "JWT", "endpoints": ["/api/v1/auth/login/", "/api/v1/auth/logout/", "/api/v1/auth/token/refresh/"]},
    "websockets": [],
    "jobs": ["create_new_reporting_period", "auto_close_reporting_periods", "send_weekly_reminders", "send_deadline_approaching", "send_overdue_summary"],
    "external_apis": []
}

with open('backend-inventory.json', 'w') as f:
    json.dump(inventory, f, indent=2)

print(f"Exported {len(endpoints)} endpoint derivations to backend-inventory.json")
