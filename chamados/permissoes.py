from django.contrib.auth.decorators import login_required, permission_required


def acesso_tecnico(*, alterar=False):
    permissoes = ['chamados.view_chamado']
    if alterar:
        permissoes.append('chamados.change_chamado')

    def decorar(view):
        return login_required(permission_required(permissoes, raise_exception=True)(view))

    return decorar
