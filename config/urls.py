from django.contrib import admin
from django.urls import include, path
from chamados.views import chamado_list_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('equipamentos/', include('equipamentos.urls', namespace='equipamentos')),
    path('chamados/', include('chamados.urls', namespace='chamados')),
    path('', chamado_list_view, name='inicio'),
]
