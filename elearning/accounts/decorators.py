from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def tutor_required(view_func):
    return role_required(['tutor', 'admin'])(view_func)

def student_required(view_func):
    return role_required(['student'])(view_func)
