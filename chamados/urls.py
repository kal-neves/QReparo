from django.urls import path
from . import views

app_name = 'chamados'

urlpatterns = [
    # Visualizações HTML
    path('', views.chamado_list_view, name='lista'),
    path('<int:pk>/', views.chamado_detail_view, name='detalhes'),
    path('<int:pk>/fotos/<uuid:foto_id>/', views.foto_relato, name='foto'),

    # Endpoints de API REST
    path('api/', views.api_chamados, name='api_lista_ou_criar'),
    path('api/<int:pk>/', views.chamado_detail_view, name='api_detalhes'),
    path('api/<int:pk>/status/', views.api_chamado_atualizar_status, name='api_atualizar_status'),
]
