import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Equipamento


def equipamento_list_view(request):
    """
    Lista todos os equipamentos com suporte a busca e filtros por status/categoria.
    Retorna template HTML ou JSON caso solicitado via Header ou parâmetro format=json.
    """
    busca = request.GET.get('busca', '').strip()
    status = request.GET.get('status', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    queryset = Equipamento.objects.all().prefetch_related('chamados')

    if busca:
        queryset = queryset.filter(
            Q(nome__icontains=busca) |
            Q(codigo_patrimonio__icontains=busca) |
            Q(localizacao__icontains=busca)
        )

    if status:
        queryset = queryset.filter(status=status)

    if categoria:
        queryset = queryset.filter(categoria=categoria)

    # Se a requisição pedir JSON
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        dados = [
            {
                'id': eq.id,
                'nome': eq.nome,
                'codigo_patrimonio': eq.codigo_patrimonio,
                'categoria': eq.categoria,
                'categoria_display': eq.get_categoria_display(),
                'localizacao': eq.localizacao,
                'status': eq.status,
                'status_display': eq.get_status_display(),
                'descricao': eq.descricao,
                'total_chamados': eq.total_chamados,
                'total_chamados_abertos': eq.total_chamados_abertos,
                'criado_em': eq.criado_em.strftime('%Y-%m-%d %H:%M:%S') if eq.criado_em else None,
            }
            for eq in queryset
        ]
        return JsonResponse({'equipamentos': dados, 'total': len(dados)})

    context = {
        'equipamentos': queryset,
        'busca': busca,
        'status_selecionado': status,
        'categoria_selecionada': categoria,
        'status_choices': Equipamento.STATUS_CHOICES,
        'categoria_choices': Equipamento.CATEGORIA_CHOICES,
    }
    return render(request, 'equipamentos/lista.html', context)


def equipamento_detail_view(request, pk):
    """
    Exibe os detalhes de um equipamento específico e o histórico de seus chamados.
    """
    equipamento = get_object_or_404(Equipamento, pk=pk)
    chamados = equipamento.chamados.all().order_by('-data_abertura')

    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': equipamento.id,
            'nome': equipamento.nome,
            'codigo_patrimonio': equipamento.codigo_patrimonio,
            'categoria': equipamento.categoria,
            'categoria_display': equipamento.get_categoria_display(),
            'localizacao': equipamento.localizacao,
            'status': equipamento.status,
            'status_display': equipamento.get_status_display(),
            'descricao': equipamento.descricao,
            'chamados': [
                {
                    'id': ch.id,
                    'titulo': ch.titulo,
                    'status': ch.status,
                    'prioridade': ch.prioridade,
                    'data_abertura': ch.data_abertura.strftime('%Y-%m-%d %H:%M:%S'),
                    'solicitante': ch.solicitante.username if ch.solicitante else None,
                }
                for ch in chamados
            ]
        })

    return render(request, 'equipamentos/detalhes.html', {
        'equipamento': equipamento,
        'chamados': chamados,
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_equipamentos(request):
    """
    Endpoint de API REST para listagem (GET) e cadastro de novos equipamentos (POST).
    """
    if request.method == "GET":
        return equipamento_list_view(request)

    # POST - Cadastro de novo equipamento
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    nome = data.get('nome')
    codigo_patrimonio = data.get('codigo_patrimonio')
    categoria = data.get('categoria', Equipamento.CATEGORIA_INFORMATICA)
    localizacao = data.get('localizacao')
    status = data.get('status', Equipamento.STATUS_OPERACIONAL)
    descricao = data.get('descricao', '')

    if not nome or not codigo_patrimonio or not localizacao:
        return JsonResponse(
            {'erro': 'Campos obrigatórios: nome, codigo_patrimonio, localizacao.'},
            status=400
        )

    if Equipamento.objects.filter(codigo_patrimonio=codigo_patrimonio).exists():
        return JsonResponse(
            {'erro': f'Já existe um equipamento cadastrado com o patrimônio {codigo_patrimonio}.'},
            status=409
        )

    equipamento = Equipamento.objects.create(
        nome=nome,
        codigo_patrimonio=codigo_patrimonio,
        categoria=categoria,
        localizacao=localizacao,
        status=status,
        descricao=descricao
    )

    return JsonResponse({
        'mensagem': 'Equipamento cadastrado com sucesso!',
        'equipamento': {
            'id': equipamento.id,
            'nome': equipamento.nome,
            'codigo_patrimonio': equipamento.codigo_patrimonio,
            'status': equipamento.status,
        }
    }, status=201)
