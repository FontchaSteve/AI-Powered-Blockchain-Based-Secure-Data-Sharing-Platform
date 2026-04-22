from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from files.views import dashboard


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',        home,                        name='home'),
    path('upload/', include('files.urls')),
    path('accounts/', include('users.urls')),
    path('ai-monitor/', include('ai_monitor.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)