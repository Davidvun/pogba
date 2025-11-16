from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from .models import UserSession

class SingleDeviceLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            session_key = request.session.session_key
            
            if session_key:
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
                ip_address = self.get_client_ip(request)
                
                active_sessions = UserSession.objects.filter(
                    user=request.user,
                    is_active=True
                ).exclude(session_key=session_key)
                
                for old_session in active_sessions:
                    try:
                        Session.objects.filter(session_key=old_session.session_key).delete()
                    except:
                        pass
                    old_session.is_active = False
                    old_session.save()
                
                user_session, created = UserSession.objects.get_or_create(
                    user=request.user,
                    session_key=session_key,
                    defaults={
                        'device_info': user_agent,
                        'ip_address': ip_address,
                        'is_active': True
                    }
                )
                
                if not created:
                    user_session.device_info = user_agent
                    user_session.ip_address = ip_address
                    user_session.is_active = True
                    user_session.save()
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
