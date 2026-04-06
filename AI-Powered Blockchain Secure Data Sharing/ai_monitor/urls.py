from django.urls import path
from .views import ai_monitor

urlpatterns = [
    path('', ai_monitor, name='ai_monitor'),
]