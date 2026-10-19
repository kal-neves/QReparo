import json
from uuid import UUID

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from equipamentos.models import Equipamento
from .models import Chamado, ConflitoEstado, Tag


def _json(request):
    return '/api/' in request.path or request.GET.get('format') == 'json' or request.headers.get('Accept') == 'application/json'


def _dados(request):
    if request.content_type == 'application/json':
        try:
            dados = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            raise ValidationError('JSON inválido.')
        if not isinstance(dados, dict):
            raise ValidationError('Envie um objeto JSON.')
        return dados
    if any(len(request.POST.getlist(key)) != 1 for key in request.POST):
        raise ValidationError('Envie somente um valor por campo.')
    return request.POST


def _serializar(chamado):
    return {
        'id': chamado.pk,
        'equipamento_id': chamado.equipamento_id,
        'laboratorio_id': chamado.laboratorio_id,
        'problema_id': chamado.problema_id,
        'problema': chamado.problema.nome,
        'descricao': chamado.descricao,
        'status': chamado.status,
        'data_abertura': chamado.data_abertura,
    }


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def chamado_list_view(request):
    """Adapta a consulta existente: apenas relatos ativos, acesso técnico."""
    chamados = Chamado.objects.filter(status=Chamado.ABERTO).select_related('problema', 'equipamento')
    equipamento = request.GET.get('equipamento')
    if equipamento:
        if not equipamento.isdecimal() or len(equipamento) > 18:
            return JsonResponse({'erro': 'Equipamento inválido.'}, status=400)
        chamados = chamados.filter(equipamento_id=int(equipamento))
    if _json(request):
        dados = [_serializar(chamado) for chamado in chamados]
        return JsonResponse({'chamados': dados, 'total': len(dados)})
    # Os templates ainda não foram implementados nesta etapa.
    return render(request, 'chamados/lista.html', {'chamados': chamados})


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def chamado_detail_view(request, pk):
    chamado = get_object_or_404(Chamado.objects.select_related('problema'), pk=pk, status=Chamado.ABERTO)
    if _json(request):
        return JsonResponse(_serializar(chamado))
    return render(request, 'chamados/detalhes.html', {'chamado': chamado})


@never_cache
@sensitive_post_parameters('descricao')
@require_http_methods(['GET', 'POST'])
def api_chamados(request):
    """Mantém o endpoint existente; não implementa formulário ou fluxo de QR."""
    if request.method == 'GET':
        return chamado_list_view(request)
    try:
        dados = _dados(request)
        token = UUID(str(dados.get('qr_token', '')))
        problema_id = dados.get('problema')
        if isinstance(problema_id, bool) or not str(problema_id).isdecimal() or len(str(problema_id)) > 18:
            raise ValidationError('Selecione exatamente um problema.')
        descricao = dados.get('descricao', '')
        if not isinstance(descricao, str):
            raise ValidationError('Descrição inválida.')
        equipamento = get_object_or_404(Equipamento, qr_token=token)
        problema = get_object_or_404(Tag, pk=int(problema_id))
        Chamado.objects.create(equipamento=equipamento, problema=problema, descricao=descricao.strip())
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Identificador de QR inválido.'}, status=400)
    except ValidationError as erro:
        return JsonResponse({'erros': erro.messages}, status=400)
    except Equipamento.DoesNotExist:
        return JsonResponse({'erro': 'Equipamento não encontrado.'}, status=404)
    # Nenhum ID consultável, autoria ou texto livre retorna ao aluno.
    return JsonResponse({'mensagem': 'Relato recebido.'}, status=201)


@never_cache
@permission_required(('chamados.view_chamado', 'chamados.change_chamado'), raise_exception=True)
@require_http_methods(['POST', 'PATCH'])
def api_chamado_atualizar_status(request, pk):
    """Resolução individual já existente, sem laudo/autoria/reabertura.

    Conferência e resolução em lote serão implementadas separadamente.
    """
    try:
        dados = _dados(request)
        if dados.get('status') != Chamado.RESOLVIDO:
            raise ValidationError('A única transição permitida é para Resolvido.')
        chamado = get_object_or_404(Chamado, pk=pk)
        chamado.status = Chamado.RESOLVIDO
        chamado.save(update_fields=['status'])
    except ConflitoEstado:
        return JsonResponse({'erro': 'O relato já foi resolvido.'}, status=409)
    except ValidationError as erro:
        return JsonResponse({'erros': erro.messages}, status=400)
    return JsonResponse({'mensagem': 'Relato resolvido; descrição removida.'})
