from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path('', views.homepage, name='homepage'),
    path("register.html", views.register, name="register"),
    path("login.html", views.login, name="login"),
  #  path("logout.html", views.logout, name="logout"),
    path('index.html', views.index, name='index'),
   # path('index/', include('users.urls')),
    path('blog.html', views.index, name='index'),
    path('about.html', views.index, name='index'),
    path('testimonial.html', views.index, name='index'),
    path('homepage.html', views.homepage, name='homepage'),
    path('statistic.html', views.statistic, name='statistic'),
    path('feed.html', views.feed, name='feed'),
    path('upload.html', views.upload, name='upload'),

]
