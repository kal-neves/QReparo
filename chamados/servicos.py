from equipamentos.models import Equipamento
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Chamado


class ConflitoSelecao(ValidationError):
    pass


def criar_relato(*, token, problema, descricao):
    equipamento = Equipamento.objects.get(qr_token=token)
    return Chamado.objects.create(
        equipamento=equipamento, problema=problema, descricao=descricao.strip(),
    )


def conferir_selecionados(*, equipamento_id, ids, bloquear=False):
    if not ids or any(type(pk) is not int or pk <= 0 for pk in ids) or len(set(ids)) != len(ids):
        raise ConflitoSelecao('Seleção inválida')
    consulta = Chamado.objects.filter(pk__in=ids).order_by('pk')
    if bloquear:
        consulta = consulta.select_for_update()
    relatos = list(consulta)
    if len(relatos) != len(ids) or any(
        relato.equipamento_id != equipamento_id or relato.status != Chamado.ABERTO
        for relato in relatos
    ):
        raise ConflitoSelecao('Confira novamente os relatos selecionados')
    return relatos


@transaction.atomic
def resolver_selecionados(*, usuario, equipamento_id, ids):
    atual = get_user_model().objects.filter(pk=usuario.pk, is_active=True).first()
    if atual is None or not atual.has_perms(['chamados.view_chamado', 'chamados.change_chamado']):
        raise PermissionDenied
    relatos = conferir_selecionados(equipamento_id=equipamento_id, ids=ids, bloquear=True)
    for relato in relatos:
        relato.status = Chamado.RESOLVIDO
        relato.save(update_fields=['status'])
    return len(relatos)
