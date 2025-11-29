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
]
