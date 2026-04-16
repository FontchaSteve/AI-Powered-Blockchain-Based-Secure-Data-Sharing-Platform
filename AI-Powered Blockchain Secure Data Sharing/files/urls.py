from django.urls import path
from .views import (
    dashboard, upload_file, my_files,
    download_file, delete_file,
    share_file, shared_with_me, download_shared_file,
    blockchain_verify,
)

urlpatterns = [
    path('dashboard/',                      dashboard,            name='dashboard'),
    path('',                                upload_file,          name='upload_file'),
    path('my-files/',                       my_files,             name='my_files'),
    path('download/<int:file_id>/',         download_file,        name='download_file'),
    path('download-shared/<int:file_id>/',  download_shared_file, name='download_shared_file'),
    path('delete/<int:file_id>/',           delete_file,          name='delete_file'),
    path('share/<int:file_id>/',            share_file,           name='share_file'),
    path('shared-with-me/',                 shared_with_me,       name='shared_with_me'),
    path('blockchain/verify/',              blockchain_verify,    name='blockchain_verify'),
]