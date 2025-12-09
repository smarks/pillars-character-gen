from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('generator/', views.index, name='generator'),
    # Note: 'index' is an alias for 'generator' for backwards compatibility
    # Both names point to the same URL pattern
    path('interactive/', views.interactive, name='interactive'),
    path('update-session-character/', views.update_session_character, name='update_session_character'),
    path('select-track/', views.select_track, name='select_track'),
    path('start-over/', views.start_over, name='start_over'),
    # Handbook sections - loaded from references/ or docs/ directory
    path('about/', views.handbook_section, {'section': 'about'}, name='about'),
    path('lore/', views.handbook_section, {'section': 'lore'}, name='lore'),
    path('handbook/', views.handbook_section, {'section': 'players_handbook'}, name='handbook'),
    path('combat/', views.handbook_section, {'section': 'combat'}, name='combat'),
    path('dm/', views.dm_handbook, name='dm'),
    # Images for handbook markdown files
    path('images/<str:filename>', views.serve_reference_image, name='reference_image'),
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # Character save/load
    path('my-characters/', views.my_characters, name='my_characters'),
    path('save-character/', views.save_character, name='save_character'),
    path('load-character/<int:char_id>/', views.load_character, name='load_character'),
    path('delete-character/<int:char_id>/', views.delete_character, name='delete_character'),
    # Editable character sheet
    path('character/<int:char_id>/', views.character_sheet, name='character_sheet'),
    path('character/<int:char_id>/update/', views.update_character, name='update_character'),
    path('character/<int:char_id>/add-experience/', views.add_experience_to_character, name='add_experience_to_character'),
    # Admin-only
    path('manage-users/', views.manage_users, name='manage_users'),
    path('change-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-delete-character/<int:char_id>/', views.admin_delete_character, name='admin_delete_character'),
]
