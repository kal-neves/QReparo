"""
Configuração de URLs do QReparo
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Painel de Administração do Django
    path('admin/', admin.site.urls),

    # Módulo de Equipamentos
    path('equipamentos/', include('equipamentos.urls', namespace='equipamentos')),

    # Módulo de Chamados
    path('chamados/', include('chamados.urls', namespace='chamados')),

    # Raiz redirecionando para a listagem ou dashboard de equipamentos
    path('', include('chamados.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
