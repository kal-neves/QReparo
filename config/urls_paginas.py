from django.urls import path
from .paginas import pagina

app_name = 'paginas'

urlpatterns = [
    path('e/<uuid:token>/', pagina, {
        'template_name': 'chamados/novo.html', 'titulo': 'Registrar problema',
    }, name='relato'),
    path('recebido/', pagina, {
        'template_name': 'chamados/confirmacao.html', 'titulo': 'Confirmação de envio',
    }, name='confirmacao'),
    path('entrar/', pagina, {
        'template_name': 'registration/login.html', 'titulo': 'Entrada técnica',
    }, name='entrada'),
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
    path('equipamentos/<int:pk>/etiqueta/', pagina, {
        'template_name': 'equipamentos/etiqueta.html', 'titulo': 'Etiqueta do equipamento',
        'permissao': 'equipamentos.view_equipamento',
    }, name='etiqueta'),
]
