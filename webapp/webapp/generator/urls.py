from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('generator/', views.index, name='generator'),
    path('generator/', views.index, name='index'),  # Alias for backwards compatibility
    path('interactive/', views.interactive, name='interactive'),
    path('select-track/', views.select_track, name='select_track'),
    path('start-over/', views.start_over, name='start_over'),
    # Handbook sections - use generic view with extracted markdown files
    path('meta/', views.handbook_section, {'section': 'meta'}, name='meta'),
    path('lore/', views.handbook_section, {'section': 'lore'}, name='lore'),
    path('handbook/', views.handbook_section, {'section': 'players_handbook'}, name='handbook'),
    path('dm/', views.handbook_section, {'section': 'DM_handbook'}, name='dm'),
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # Character save/load
    path('my-characters/', views.my_characters, name='my_characters'),
    path('save-character/', views.save_character, name='save_character'),
    path('load-character/<int:char_id>/', views.load_character, name='load_character'),
    path('delete-character/<int:char_id>/', views.delete_character, name='delete_character'),
    # DM-only
    path('manage-users/', views.manage_users, name='manage_users'),
    path('change-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
]
