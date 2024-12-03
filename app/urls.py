from django.urls import path
from . import views


urlpatterns = [
    # path('', views.home,  name='home'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('myemails', views.myemails,  name='myemails'),
    path('ats', views.ats,  name='ats'),
    path('send', views.send,  name='send'),
    path('', views.hiring_page,  name='hiring_page'),
    path('job_create', views.job_create,  name='job_create'),
]