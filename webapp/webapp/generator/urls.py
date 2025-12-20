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
    path('dice/', views.dice_roller, name='dice_roller'),
    # Handbook sections - loaded from references/ directory
    path('about/', views.handbook_section, {'section': 'about'}, name='about'),
    path('lore/', views.handbook_section, {'section': 'lore'}, name='lore'),
    path('handbook/', views.handbook_section, {'section': 'players_handbook'}, name='handbook'),
    path('combat/', views.handbook_section, {'section': 'combat'}, name='combat'),
    path('dm/', views.dm_handbook, name='dm'),
    path('rulebook/', views.handbook_section, {'section': 'public_rulebook'}, name='rulebook'),
    path('turn-sequence/', views.serve_reference_html, {'filename': 'pillars-turn-sequence.html'}, name='turn_sequence'),
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
    # User notes
    path('notes/', views.user_notes, name='notes'),
    path('save-notes/', views.save_user_notes, name='save_user_notes'),
    # Editable character sheet
    path('character/<int:char_id>/', views.character_sheet, name='character_sheet'),
    path('character/<int:char_id>/update/', views.update_character, name='update_character'),
    path('character/<int:char_id>/add-experience/', views.add_experience_to_character, name='add_experience_to_character'),
    # Admin/DM management
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-characters/', views.manage_characters, name='manage_characters'),
    path('manage-characters/bulk-delete/', views.bulk_delete_characters, name='bulk_delete_characters'),
    path('admin-notes/', views.admin_notes, name='admin_notes'),
    path('admin-notes/<int:note_id>/edit/', views.admin_edit_note, name='admin_edit_note'),
    path('admin-notes/<int:note_id>/delete/', views.admin_delete_note, name='admin_delete_note'),
    path('change-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-delete-character/<int:char_id>/', views.admin_delete_character, name='admin_delete_character'),
]
