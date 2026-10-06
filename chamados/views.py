import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Chamado
from equipamentos.models import Equipamento

User = get_user_model()


def chamado_list_view(request):
    """
    Lista todos os chamados com filtros por status, prioridade e busca por texto.
    Suporta visualização em template HTML ou formato JSON.
    """
    status = request.GET.get('status', '').strip()
    prioridade = request.GET.get('prioridade', '').strip()
    busca = request.GET.get('busca', '').strip()
    equipamento_id = request.GET.get('equipamento', '').strip()

    queryset = Chamado.objects.select_related('equipamento', 'solicitante', 'tecnico_responsavel').all()

    if status:
        queryset = queryset.filter(status=status)
    if prioridade:
        queryset = queryset.filter(prioridade=prioridade)
    if equipamento_id:
        queryset = queryset.filter(equipamento_id=equipamento_id)
    if busca:
        queryset = queryset.filter(
            titulo__icontains=busca
        ) | queryset.filter(
            descricao__icontains=busca
        ) | queryset.filter(
            equipamento__nome__icontains=busca
        ) | queryset.filter(
            equipamento__codigo_patrimonio__icontains=busca
        )

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        dados = [
            {
                'id': ch.id,
                'titulo': ch.titulo,
                'descricao': ch.descricao,
                'equipamento': {
                    'id': ch.equipamento.id,
                    'nome': ch.equipamento.nome,
                    'codigo_patrimonio': ch.equipamento.codigo_patrimonio,
                    'localizacao': ch.equipamento.localizacao,
                },
                'solicitante': ch.solicitante.username if ch.solicitante else None,
                'solicitante_nome': ch.solicitante.get_full_name() or ch.solicitante.username if ch.solicitante else None,
                'tecnico_responsavel': ch.tecnico_responsavel.username if ch.tecnico_responsavel else None,
                'tecnico_nome': ch.tecnico_responsavel.get_full_name() or ch.tecnico_responsavel.username if ch.tecnico_responsavel else None,
                'prioridade': ch.prioridade,
                'prioridade_display': ch.get_prioridade_display(),
                'status': ch.status,
                'status_display': ch.get_status_display(),
                'laudo_tecnico': ch.laudo_tecnico,
                'data_abertura': ch.data_abertura.strftime('%Y-%m-%d %H:%M:%S'),
                'data_conclusao': ch.data_conclusao.strftime('%Y-%m-%d %H:%M:%S') if ch.data_conclusao else None,
            }
            for ch in queryset
        ]
        return JsonResponse({'chamados': dados, 'total': len(dados)})

    context = {
        'chamados': queryset,
        'status_selecionado': status,
        'prioridade_selecionada': prioridade,
        'status_choices': Chamado.STATUS_CHOICES,
        'prioridade_choices': Chamado.PRIORIDADE_CHOICES,
    }
    return render(request, 'chamados/lista.html', context)


def chamado_detail_view(request, pk):
    """
    Exibe os detalhes de um chamado específico e opções para emitir laudo técnico.
    """
    chamado = get_object_or_404(
        Chamado.objects.select_related('equipamento', 'solicitante', 'tecnico_responsavel'),
        pk=pk
    )

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': chamado.id,
            'titulo': chamado.titulo,
            'descricao': chamado.descricao,
            'equipamento_id': chamado.equipamento.id,
            'equipamento_nome': chamado.equipamento.nome,
            'equipamento_patrimonio': chamado.equipamento.codigo_patrimonio,
            'equipamento_localizacao': chamado.equipamento.localizacao,
            'solicitante': chamado.solicitante.username,
            'tecnico_responsavel': chamado.tecnico_responsavel.username if chamado.tecnico_responsavel else None,
            'prioridade': chamado.prioridade,
            'status': chamado.status,
            'laudo_tecnico': chamado.laudo_tecnico,
            'data_abertura': chamado.data_abertura.strftime('%Y-%m-%d %H:%M:%S'),
            'data_conclusao': chamado.data_conclusao.strftime('%Y-%m-%d %H:%M:%S') if chamado.data_conclusao else None,
        })

    return render(request, 'chamados/detalhes.html', {'chamado': chamado})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_chamados(request):
    """
    Endpoint de API REST para listar (GET) e abrir novos chamados (POST).
    """
    if request.method == "GET":
        return chamado_list_view(request)

    # POST - Abertura de chamado
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    titulo = data.get('titulo')
    descricao = data.get('descricao')
    equipamento_id = data.get('equipamento_id') or data.get('equipamento')
    codigo_patrimonio = data.get('codigo_patrimonio')
    prioridade = data.get('prioridade', Chamado.PRIORIDADE_MEDIA)

    if not titulo or not descricao:
        return JsonResponse(
            {'erro': 'Os campos título e descrição são obrigatórios.'},
            status=400
        )

    # Localiza o equipamento por ID ou por código de patrimônio
    equipamento = None
    if equipamento_id:
        try:
            equipamento = Equipamento.objects.get(pk=equipamento_id)
        except Equipamento.DoesNotExist:
            return JsonResponse({'erro': f'Equipamento com ID {equipamento_id} não encontrado.'}, status=404)
    elif codigo_patrimonio:
        try:
            equipamento = Equipamento.objects.get(codigo_patrimonio=codigo_patrimonio)
        except Equipamento.DoesNotExist:
            return JsonResponse({'erro': f'Patrimônio {codigo_patrimonio} não encontrado.'}, status=404)
    else:
        return JsonResponse({'erro': 'Informe o equipamento_id ou codigo_patrimonio.'}, status=400)

    # Define o solicitante: usuário autenticado ou usuário padrão/fallback do sistema
    solicitante = None
    if request.user.is_authenticated:
        solicitante = request.user
    else:
        # Se requisição anônima na API, busca usuário informado ou o primeiro usuário/admin
        username_solicitante = data.get('solicitante_username')
        if username_solicitante:
            solicitante = User.objects.filter(username=username_solicitante).first()
        if not solicitante:
            solicitante = User.objects.first()
            if not solicitante:
                # Cria usuário padrão de serviço se o banco estiver vazio
                solicitante = User.objects.create_user(
                    username='solicitante_padrao',
                    email='usuario@universidade.edu.br',
                    first_name='Usuário',
                    last_name='Acadêmico'
                )

    chamado = Chamado.objects.create(
        titulo=titulo,
        descricao=descricao,
        equipamento=equipamento,
        solicitante=solicitante,
        prioridade=prioridade,
        status=Chamado.STATUS_ABERTO
    )

    return JsonResponse({
        'mensagem': 'Chamado aberto com sucesso!',
        'chamado': {
            'id': chamado.id,
            'titulo': chamado.titulo,
            'equipamento': chamado.equipamento.nome,
            'patrimonio': chamado.equipamento.codigo_patrimonio,
            'prioridade': chamado.prioridade,
            'status': chamado.status,
            'data_abertura': chamado.data_abertura.strftime('%Y-%m-%d %H:%M:%S'),
        }
    }, status=201)


@csrf_exempt
@require_http_methods(["POST", "PATCH"])
def api_chamado_atualizar_status(request, pk):
    """
    Endpoint para atualizar o status e/ou preencher laudo técnico de um chamado.
    """
    chamado = get_object_or_404(Chamado, pk=pk)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    novo_status = data.get('status')
    laudo = data.get('laudo_tecnico')
    tecnico_username = data.get('tecnico_username')

    if novo_status and novo_status in dict(Chamado.STATUS_CHOICES):
        chamado.status = novo_status

    if laudo is not None:
        chamado.laudo_tecnico = laudo

    if tecnico_username:
        tecnico = User.objects.filter(username=tecnico_username).first()
        if tecnico:
            chamado.tecnico_responsavel = tecnico
    elif request.user.is_authenticated:
        chamado.tecnico_responsavel = request.user

    chamado.save()

    return JsonResponse({
        'mensagem': f'Chamado #{chamado.id} atualizado com sucesso.',
        'chamado': {
            'id': chamado.id,
            'status': chamado.status,
            'status_display': chamado.get_status_display(),
            'laudo_tecnico': chamado.laudo_tecnico,
            'data_conclusao': chamado.data_conclusao.strftime('%Y-%m-%d %H:%M:%S') if chamado.data_conclusao else None,
            'equipamento_status': chamado.equipamento.status,
        }
    })
