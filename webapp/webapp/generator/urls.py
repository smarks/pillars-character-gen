from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('interactive/', views.interactive, name='interactive'),
    path('select-track/', views.select_track, name='select_track'),
    path('start-over/', views.start_over, name='start_over'),
]
