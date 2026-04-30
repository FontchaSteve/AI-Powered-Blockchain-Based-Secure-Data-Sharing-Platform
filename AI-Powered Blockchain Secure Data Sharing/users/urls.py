from django.urls import path
from . import views

urlpatterns = [
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),
    path('profile/',  views.profile_view,  name='profile'),

    # Custom admin panel (superusers only)
    path('manage/',                         views.admin_dashboard,    name='admin_dashboard'),
    path('manage/user/<int:user_id>/',      views.admin_user_detail,  name='admin_user_detail'),
    path('manage/delete-file/<int:file_id>/',views.admin_delete_file, name='admin_delete_file'),
]