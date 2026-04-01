from django.urls import path
from .views import upload_file, my_files

urlpatterns = [
    path('', upload_file, name='upload_file'),
    path('my-files/', my_files, name='my_files'),
]