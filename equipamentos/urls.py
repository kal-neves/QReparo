from django.urls import path
from . import views

app_name = 'equipamentos'

urlpatterns = [
    # Visualização HTML / Templates
    path('', views.equipamento_list_view, name='lista'),
    path('<int:pk>/', views.equipamento_detail_view, name='detalhes'),

    # Endpoints de API REST
    path('api/', views.api_equipamentos, name='api_lista'),
    path('api/<int:pk>/', views.equipamento_detail_view, name='api_detalhes'),
]
