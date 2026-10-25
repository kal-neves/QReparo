from urllib.parse import urlsplit

from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.urls import Resolver404, resolve, reverse


def destino_interno(usuario):
    if usuario.has_perm('chamados.view_chamado'):
        return reverse('paginas:painel')
    if usuario.is_active and usuario.is_staff:
        return reverse('admin:index')
    raise PermissionDenied


class EntradaView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        destino = self.get_redirect_url()
        permissoes = {
            'paginas:painel': 'chamados.view_chamado',
            'paginas:relatos_equipamento': 'chamados.view_chamado',
            'paginas:contagem': 'chamados.view_chamado',
            'paginas:etiqueta': 'equipamentos.view_equipamento',
        }
        if destino:
            try:
                rota = resolve(urlsplit(destino).path)
            except Resolver404:
                pass
            else:
                permissao = permissoes.get(rota.view_name)
                if permissao and self.request.user.has_perm(permissao):
                    return destino
        return destino_interno(self.request.user)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        form = contexto['form']
        contexto['login_error'] = form.is_bound and bool(form.errors)
        contexto['username'] = form['username'].value() or ''
        contexto['session_expired'] = bool(self.request.GET.get('next'))
        return contexto
