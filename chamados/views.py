import json
from uuid import UUID

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from equipamentos.models import Equipamento
from .models import Chamado, Foto, Tag
from .fotos import arquivos_do_envio
from .forms import RelatoForm, campos_fotos
from .servicos import criar_relato


@never_cache
@sensitive_post_parameters('descricao')
@require_http_methods(['GET', 'POST'])
def novo_relato(request, token):
    equipamento = Equipamento.objects.select_related('local__laboratorio').filter(qr_token=token).first()
    contexto = {'titulo': 'Registrar problema', 'equipamento': equipamento, 'internal': False}
    if equipamento is None:
        return render(request, 'chamados/novo.html', {**contexto, 'estado_visual': 'invalido'}, status=404)
    if not equipamento.ativo:
        return render(request, 'chamados/novo.html', {**contexto, 'estado_visual': 'inativo'}, status=403)
    form = RelatoForm(request.POST if request.method == 'POST' else None)
    contexto['form'] = form
    contexto['photo_fields'] = campos_fotos()
    contexto['photos_reselect'] = request.method == 'POST' and bool(request.FILES)
    if not form.fields['problema'].queryset.exists():
        return render(request, 'chamados/novo.html', {**contexto, 'estado_visual': 'sem-opcoes'}, status=503)
    if request.method == 'POST' and form.is_valid():
        try:
            criar_relato(token=token, fotos=arquivos_do_envio(request), **form.cleaned_data)
        except Equipamento.DoesNotExist:
            return render(request, 'chamados/novo.html', {**contexto, 'estado_visual': 'invalido'}, status=404)
        except ValidationError as erro:
            form.add_error(None, 'Não foi possível enviar o relato Confira o equipamento e tente novamente')
            form.add_error(None, erro)
        else:
            return redirect('paginas:confirmacao')
    return render(request, 'chamados/novo.html', contexto)


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
        'fotos': [
            {'id': foto.pk, 'url': foto.get_absolute_url(), 'posicao': foto.posicao,
             'largura': foto.largura, 'altura': foto.altura, 'tamanho': foto.tamanho}
            for foto in chamado.fotos.all()
        ],
    }


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def chamado_list_view(request):
    """Adapta a consulta existente: apenas relatos ativos, acesso técnico."""
    chamados = Chamado.objects.filter(status=Chamado.ABERTO).select_related('problema', 'equipamento').prefetch_related('fotos')
    equipamento = request.GET.get('equipamento')
    if equipamento:
        if not equipamento.isdecimal() or len(equipamento) > 18:
            return JsonResponse({'erro': 'Equipamento inválido.'}, status=400)
        chamados = chamados.filter(equipamento_id=int(equipamento))
    if _json(request):
        dados = [_serializar(chamado) for chamado in chamados]
        return JsonResponse({'chamados': dados, 'total': len(dados)})
    return redirect('paginas:painel')


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def chamado_detail_view(request, pk):
    chamado = get_object_or_404(Chamado.objects.select_related('problema'), pk=pk, status=Chamado.ABERTO)
    if _json(request):
        return JsonResponse(_serializar(chamado))
    return redirect('paginas:relatos_equipamento', pk=chamado.equipamento_id)


@never_cache
@sensitive_post_parameters('descricao')
@require_http_methods(['GET', 'POST'])
def api_chamados(request):
    """Mantém o endpoint existente; não implementa formulário ou fluxo de QR."""
    if request.method == 'GET':
        return chamado_list_view(request)
    try:
        dados = _dados(request)
        if request.content_type == 'application/json' and 'fotos' in dados:
            raise ValidationError('Para enviar fotos, use multipart/form-data com o campo fotos.')
        token = UUID(str(dados.get('qr_token', '')))
        problema_id = dados.get('problema')
        if isinstance(problema_id, bool) or not str(problema_id).isdecimal() or len(str(problema_id)) > 18:
            raise ValidationError('Selecione exatamente um problema.')
        descricao = dados.get('descricao', '')
        if not isinstance(descricao, str):
            raise ValidationError('Descrição inválida.')
        problema = get_object_or_404(Tag, pk=int(problema_id))
        criar_relato(token=token, problema=problema, descricao=descricao, fotos=arquivos_do_envio(request))
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Identificador de QR inválido.'}, status=400)
    except ValidationError as erro:
        return JsonResponse({'erros': erro.messages}, status=400)
    except Equipamento.DoesNotExist:
        return JsonResponse({'erro': 'Equipamento não encontrado.'}, status=404)
    # Nenhum ID consultável, autoria ou texto livre retorna ao aluno.
    return JsonResponse({'mensagem': 'Relato recebido.'}, status=201)


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def foto_relato(request, pk, foto_id):
    foto = get_object_or_404(Foto, pk=foto_id, chamado_id=pk,
                             chamado__status=Chamado.ABERTO, chamado__conteudo_removido=False)
    try:
        arquivo = foto.arquivo.open('rb')
    except FileNotFoundError as erro:
        raise Http404('Foto indisponível.') from erro
    resposta = FileResponse(arquivo, content_type='image/webp', filename='foto.webp')
    resposta['X-Content-Type-Options'] = 'nosniff'
    resposta['Content-Security-Policy'] = "default-src 'none'; sandbox"
    return resposta


@never_cache
@permission_required(('chamados.view_chamado', 'chamados.change_chamado'), raise_exception=True)
@require_http_methods(['POST', 'PATCH'])
def api_chamado_atualizar_status(request, pk):
    return JsonResponse({'erro': 'Use a seleção e conferência na área técnica para resolver relatos'}, status=410)
