from django.urls import path

from . import views

app_name = 'user'

urlpatterns = [
    path('', views.CreateUserView.as_view(), name='create'),
    path('auth/', views.CreateTokenView.as_view(), name='token')
]