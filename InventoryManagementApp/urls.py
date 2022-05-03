from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import profile, RegisterView

urlpatterns = [

    path('', views.index, name='index'),
  #  path('homepage.html', views.homepage, name='homepage'),
    path('statistic.html', views.statistic, name='statistic'),
    path('feed.html', views.feed, name='feed'),
    path('upload.html', views.upload, name='upload'),
    path('register.html', views.RegisterView.as_view(), name='register'),
    path('profile.html', views.profile, name='profile'),

    path('index.html', views.index, name='index'),


    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
]
