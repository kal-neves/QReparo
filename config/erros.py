from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import Resolver404, resolve, reverse
from django.views.decorators.cache import never_cache


def pagina_erro(request, *, status, titulo, texto, detalhe='', retorno=None):
    usuario = None if status == 500 else getattr(request, 'user', None)
    tecnico = bool(usuario and usuario.has_perm('chamados.view_chamado'))
    action_url = reverse('paginas:painel') if tecnico else None
    action_label = 'Voltar ao painel' if tecnico else None
    if retorno:
        action_url = retorno
        action_label = 'Abrir formulário novamente'
    contexto = {
        'state_title': titulo, 'state_text': texto, 'state_detail': detalhe,
        'state_icon': 'warning', 'minimal_header': status == 500,
        'technical': tecnico, 'backend_connected': True,
        'show_exit': bool(usuario and usuario.is_authenticated and not tecnico),
        'action_url': action_url, 'action_label': action_label,
    }
    if status == 500:
        return HttpResponse(render_to_string('paginas/estado.html', contexto), status=status)
    return render(request, 'paginas/estado.html', contexto, status=status)


@never_cache
def acesso_negado(request, exception=None):
    return pagina_erro(request, status=403, titulo='Acesso não permitido',
                       texto='Sua conta não tem permissão para acessar esta página')


@never_cache
def nao_encontrado(request, exception=None):
    return pagina_erro(request, status=404, titulo='Página não encontrada',
                       texto='Não foi possível encontrar esta página')


@never_cache
def erro_interno(request):
    return pagina_erro(request, status=500, titulo='Não foi possível concluir',
                       texto='Tente novamente mais tarde',
                       detalhe='Consulte o estado atual dos relatos antes de repetir uma resolução')


@never_cache
def csrf_rejeitado(request, reason=''):
    retorno = None
    try:
        rota = resolve(request.path_info)
    except Resolver404:
        pass
    else:
        if rota.view_name in ('paginas:relato', 'paginas:entrada'):
            retorno = reverse(rota.view_name, kwargs=rota.kwargs)
    return pagina_erro(request, status=403, titulo='Não foi possível enviar',
                       texto='Abra o formulário novamente e tente de novo', retorno=retorno)
