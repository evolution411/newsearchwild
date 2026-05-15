from django.urls import path
from . import views

app_name = 'animals'

urlpatterns = [
    path('', views.home, name='home'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('animals/', views.animal_list, name='animal_list'),
    path('animals/<int:animal_id>/', views.animal_detail, name='animal_detail'),
    path('places/', views.place_search, name='place_search'),
    path('categories/', views.category_list, name='category_list'),
    path("game/puzzle/", views.puzzle_game_home, name="puzzle_game_home"),
    path("game/puzzle/<int:animal_id>/", views.puzzle_game, name="puzzle_game"),
    path("videos/", views.video_list, name="video_list"),

]
