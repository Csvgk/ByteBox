from django.urls import path

from . import views

app_name = 'builder'

urlpatterns = [
    path('builds/', views.build_list, name='build_list'),
    path('builds/<slug:slug>/', views.build_detail, name='build_detail'),
    path('builds/<slug:slug>/to-cart/', views.build_add_to_cart, name='build_add_to_cart'),
    path('builds/<slug:slug>/edit/', views.build_update, name='build_update'),
    path('builds/<slug:slug>/delete/', views.build_delete, name='build_delete'),
    path('configurator/', views.configurator, name='configurator'),
    path('configurator/choose/<str:slot>/', views.configurator_choose, name='configurator_choose'),
    path('configurator/remove/<str:slot>/', views.configurator_remove, name='configurator_remove'),
    path('configurator/reset/', views.configurator_reset, name='configurator_reset'),
    path('configurator/to-cart/', views.configurator_to_cart, name='configurator_to_cart'),
    path('configurator/save/', views.configurator_save, name='configurator_save'),
    path('configurator/load/<slug:slug>/', views.configurator_load, name='configurator_load'),
]
