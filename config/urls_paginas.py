from django.urls import path
from django.contrib.auth.views import LogoutView
from .acesso import EntradaView
from .paginas import pagina
from equipamentos.views import etiqueta
from chamados.views import novo_relato

app_name = 'paginas'

urlpatterns = [
    path('e/<uuid:token>/', novo_relato, name='relato'),
    path('recebido/', pagina, {
        'template_name': 'chamados/confirmacao.html', 'titulo': 'Confirmação de envio',
    }, name='confirmacao'),
    path('entrar/', EntradaView.as_view(), name='entrada'),
    path('sair/', LogoutView.as_view(), name='saida'),
    path('tecnico/', pagina, {
        'template_name': 'chamados/painel.html', 'titulo': 'Equipamentos com chamados',
        'permissao': 'chamados.view_chamado',
    }, name='painel'),
    path('tecnico/equipamentos/<int:pk>/', pagina, {
        'template_name': 'chamados/detalhe.html', 'titulo': 'Relatos do equipamento',
        'permissao': 'chamados.view_chamado',
    }, name='relatos_equipamento'),
    path('tecnico/equipamentos/<int:pk>/conferencia/', pagina, {
        'template_name': 'chamados/resolver.html', 'titulo': 'Conferência da resolução',
        'permissao': ('chamados.view_chamado', 'chamados.change_chamado'),
    }, name='conferencia'),
    path('tecnico/contagem/', pagina, {
        'template_name': 'chamados/contagem.html', 'titulo': 'Contagem técnica',
        'permissao': 'chamados.view_chamado',
    }, name='contagem'),
    path('equipamentos/<int:pk>/etiqueta/', etiqueta, name='etiqueta'),
]
