from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.exceptions import ThrottleException


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts"""
    scope = 'login'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return None  # Don't throttle authenticated users

        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def throttle_failure(self):
        raise ThrottleException({
            'error': 'Too many login attempts. Please try again later.',
            'code': 'login_throttle_exceeded'
        })


class ReportSubmitRateThrottle(UserRateThrottle):
    """Rate limit for report submissions"""
    scope = 'reports'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
