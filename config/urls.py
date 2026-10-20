from django.contrib import admin
from django.urls import include, path
from .paginas import inicio

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('config.urls_paginas')),
    path('equipamentos/', include('equipamentos.urls', namespace='equipamentos')),
    path('chamados/', include('chamados.urls', namespace='chamados')),
    path('', inicio, name='inicio'),
]
