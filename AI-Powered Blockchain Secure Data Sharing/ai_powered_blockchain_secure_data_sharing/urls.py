from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Root URL - Always show Login first if not logged in
def home(request):
    if request.user.is_authenticated:
        return redirect('my_files')      # Logged in → go to My Files (temporary dashboard)
    else:
        return redirect('login')         # Not logged in → go to Login page

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', home, name='home'),                    # Root URL
    
    # File routes
    path('upload/', include('files.urls')),
    
    # Authentication routes
    path('accounts/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)