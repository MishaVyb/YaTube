from django.http import HttpResponseForbidden
from django.shortcuts import render


def page_forbidden(request, exception):
    """Handling 403 HTTP status"""
    render(request, 'core/403csrf.html', status=403)


def page_not_found(request, exception):
    """Handling 404 HTTP status"""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    """Handling 500 HTTP status"""
    return render(request, 'core/500.html', {}, status=500)


def csrf_failure(request, reason=''):
    return HttpResponseForbidden()
