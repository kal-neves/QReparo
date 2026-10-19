from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .models import Equipamento


def _json(request):
    return '/api/' in request.path or request.GET.get('format') == 'json' or request.headers.get('Accept') == 'application/json'


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def equipamento_list_view(request):
    equipamentos = Equipamento.objects.select_related('local__laboratorio').annotate(
        abertos=Count('chamados', filter=Q(chamados__status='ABERTO'))).filter(abertos__gt=0)
    if _json(request):
        dados = [{
            'id': eq.pk, 'nome': eq.nome, 'codigo_patrimonio': eq.codigo_patrimonio,
            'laboratorio': eq.local.laboratorio.nome, 'local': eq.local.nome,
            'total_chamados_abertos': eq.abertos,
        } for eq in equipamentos]
        return JsonResponse({'equipamentos': dados, 'total': len(dados)})
    return render(request, 'equipamentos/lista.html', {'equipamentos': equipamentos})


@never_cache
@permission_required('chamados.view_chamado', raise_exception=True)
@require_http_methods(['GET'])
def equipamento_detail_view(request, pk):
    equipamento = get_object_or_404(Equipamento.objects.select_related('local__laboratorio'), pk=pk)
    chamados = equipamento.chamados.filter(status='ABERTO').select_related('problema')
    if _json(request):
        return JsonResponse({
            'id': equipamento.pk, 'nome': equipamento.nome, 'descricao': equipamento.descricao,
            'codigo_patrimonio': equipamento.codigo_patrimonio,
            'laboratorio': equipamento.local.laboratorio.nome, 'local': equipamento.local.nome,
            'chamados': [{'id': ch.pk, 'problema': ch.problema.nome, 'descricao': ch.descricao,
                          'data_abertura': ch.data_abertura} for ch in chamados],
        })
    return render(request, 'equipamentos/detalhes.html', {'equipamento': equipamento, 'chamados': chamados})


@require_http_methods(['GET'])
def api_equipamentos(request):
    # Cadastro permanece no Django Admin; a API anterior não deve contorná-lo.
    return equipamento_list_view(request)
