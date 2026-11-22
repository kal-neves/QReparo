from django.urls import path
from django.contrib.auth.views import LogoutView
from .acesso import EntradaView
from .paginas import pagina
from equipamentos.views import etiqueta
from chamados.views import novo_relato
from chamados import atendimento

app_name = 'paginas'

urlpatterns = [
    path('e/<uuid:token>/', novo_relato, name='relato'),
    path('recebido/', pagina, {
        'template_name': 'chamados/confirmacao.html', 'titulo': 'Confirmação de envio',
    }, name='confirmacao'),
    path('entrar/', EntradaView.as_view(), name='entrada'),
    path('sair/', LogoutView.as_view(), name='saida'),
    path('tecnico/', atendimento.painel, name='painel'),
    path('tecnico/relatos/<int:pk>/fotos/<uuid:foto_id>/', atendimento.visualizar_foto, name='foto_relato'),
    path('tecnico/equipamentos/<int:pk>/', atendimento.detalhe, name='relatos_equipamento'),
    path('tecnico/equipamentos/<int:pk>/conferencia/', atendimento.conferencia, name='conferencia'),
    path('tecnico/equipamentos/<int:pk>/resolver/', atendimento.resolver, name='resolver'),
    path('tecnico/contagem/', atendimento.contagem, name='contagem'),
    path('equipamentos/<int:pk>/etiqueta/', etiqueta, name='etiqueta'),
]
