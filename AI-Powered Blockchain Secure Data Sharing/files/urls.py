from django.urls import path
from .views import dashboard, upload_file, my_files, download_file, delete_file

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),           # Main Dashboard
    path('', upload_file, name='upload_file'),
    path('my-files/', my_files, name='my_files'),
    path('download/<int:file_id>/', download_file, name='download_file'),
    path('delete/<int:file_id>/', delete_file, name='delete_file'),
]