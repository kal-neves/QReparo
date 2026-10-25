"""entrada e páginas ainda em integração"""
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.loader import select_template
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from .acesso import destino_interno


@require_safe
def inicio(request):
    destino = destino_interno(request.user) if request.user.is_authenticated else 'paginas:entrada'
    return redirect(destino)


@never_cache
@require_safe
def pagina(request, *, template_name, titulo, permissao=None, **parametros):
    permissoes = (permissao,) if isinstance(permissao, str) else permissao
    if permissoes and not request.user.has_perms(permissoes):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        raise PermissionDenied
    template = select_template([template_name, 'paginas/pendente.html'])
    return HttpResponse(template.render({
        'titulo': titulo,
        'template_previsto': template_name,
        'parametros_rota': parametros,
        'internal': bool(permissoes),
        'desktop': bool(permissoes) or template_name == 'registration/login.html',
        'active_nav': 'contagem' if template_name == 'chamados/contagem.html' else 'painel',
    }, request))
