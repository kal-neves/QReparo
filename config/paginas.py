"""Pontos de entrada para o frontend, sem consultas ou ações de negócio."""
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.loader import select_template
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@require_safe
def inicio(request):
    destino = 'paginas:painel' if request.user.is_authenticated else 'paginas:entrada'
    return redirect(destino)


@never_cache
@require_safe
def pagina(request, *, template_name, titulo, permissao=None, **parametros):
    permissoes = (permissao,) if isinstance(permissao, str) else permissao
    if permissoes and not request.user.has_perms(permissoes):
        raise PermissionDenied
    template = select_template([template_name, 'paginas/pendente.html'])
    return HttpResponse(template.render({
        'titulo': titulo,
        'template_previsto': template_name,
        'parametros_rota': parametros,
    }, request))
