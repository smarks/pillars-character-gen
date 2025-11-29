from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('generator/', views.index, name='generator'),
    path('generator/', views.index, name='index'),  # Alias for backwards compatibility
    path('interactive/', views.interactive, name='interactive'),
    path('select-track/', views.select_track, name='select_track'),
    path('start-over/', views.start_over, name='start_over'),
    path('lore/', views.lore, name='lore'),
    path('handbook/', views.handbook, name='handbook'),
]
