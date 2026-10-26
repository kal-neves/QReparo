from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from .paginas import inicio

handler403 = 'config.erros.acesso_negado'
handler404 = 'config.erros.nao_encontrado'
handler500 = 'config.erros.erro_interno'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('config.urls_paginas')),
    path('equipamentos/', include('equipamentos.urls', namespace='equipamentos')),
    path('chamados/', include('chamados.urls', namespace='chamados')),
    path('', inicio, name='inicio'),
]

if settings.DEBUG:
    from .ui_preview import preview
    urlpatterns += [path('_ui/', preview, name='ui-preview')]
