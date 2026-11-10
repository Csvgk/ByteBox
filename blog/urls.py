from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('new/', views.post_create, name='post_create'),
    path('comments/<int:pk>/edit/', views.comment_update, name='comment_update'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
    path('<slug:slug>/edit/', views.post_update, name='post_update'),
    path('<slug:slug>/delete/', views.post_delete, name='post_delete'),
]
