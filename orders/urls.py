from django.urls import path
from . import views

urlpatterns = [
    path('place_orders', views.place_orders, name='place_orders'),
    path('payments/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
]