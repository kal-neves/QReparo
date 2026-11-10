from equipamentos.models import Equipamento
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Chamado, Foto
from .fotos import apagar_arquivo, preparar_fotos


class ConflitoSelecao(ValidationError):
    pass


def criar_relato(*, token, problema, descricao, fotos=()):
    preparadas = preparar_fotos(fotos)
    salvos = []
    try:
        with transaction.atomic(durable=True):
            equipamento = Equipamento.objects.get(qr_token=token)
            chamado = Chamado.objects.create(
                equipamento=equipamento, problema=problema, descricao=descricao.strip(),
            )
            for posicao, (conteudo, largura, altura) in enumerate(preparadas, start=1):
                foto = Foto(chamado=chamado, posicao=posicao, largura=largura,
                            altura=altura, tamanho=conteudo.size)
                nome = foto.arquivo.field.generate_filename(foto, 'foto.webp')
                salvos.append((foto.arquivo.storage, nome))
                foto.arquivo.name = foto.arquivo.storage.save(nome, conteudo)
                salvos[-1] = (foto.arquivo.storage, foto.arquivo.name)
                foto.save()
            return chamado
    except Exception as erro:
        for storage, nome in salvos:
            apagar_arquivo(storage, nome)
        if isinstance(erro, OSError):
            raise ValidationError('Não foi possível salvar as fotos. Tente novamente.') from erro
        raise


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
