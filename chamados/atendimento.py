from django.contrib import messages
from django.core import signing
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from equipamentos.models import Equipamento
from .consultas import contagem_tecnica, equipamentos_com_abertos, relatos_abertos
from .forms import SelecaoResolucaoForm
from .models import Chamado
from .permissoes import acesso_tecnico
from .servicos import ConflitoSelecao, conferir_selecionados, resolver_selecionados


def equipamento_por_id(pk):
    return get_object_or_404(Equipamento.objects.select_related('local__laboratorio'), pk=pk)


def assinatura_da_sessao(request):
    return f'resolucao:{request.user.pk}:{request.session.session_key}'


@never_cache
@acesso_tecnico()
@require_GET
def painel(request):
    rows = [{
        'cells': [eq.codigo_patrimonio, eq.local.laboratorio.nome, eq.local.nome, eq.abertos],
        'description': eq.nome, 'icon': 'monitor', 'action_label': 'Ver relatos',
        'url': reverse('paginas:relatos_equipamento', args=[eq.pk]),
    } for eq in equipamentos_com_abertos()]
    return render(request, 'chamados/painel.html', {
        'rows': rows, 'columns': ['Equipamento', 'Laboratório', 'Localização', 'Relatos abertos'],
        'backend_connected': True,
    })


@never_cache
@acesso_tecnico()
@require_GET
def detalhe(request, pk):
    equipamento = equipamento_por_id(pk)
    reports = [{
        'id': relato.pk, 'problem': relato.problema.nome,
        'opened_at': timezone.localtime(relato.data_abertura),
        'laboratory': relato.laboratorio.nome, 'description': relato.descricao,
    } for relato in relatos_abertos(equipamento)]
    return render(request, 'chamados/detalhe.html', {
        'equipamento': equipamento, 'reports': reports, 'equipment_inactive': not equipamento.ativo,
        'can_resolve': request.user.has_perm('chamados.change_chamado'), 'backend_connected': True,
    })


@never_cache
@acesso_tecnico(alterar=True)
@require_POST
def conferencia(request, pk):
    equipamento = equipamento_por_id(pk)
    form = SelecaoResolucaoForm(request.POST)
    contexto = {'equipamento': equipamento, 'backend_connected': True}
    if not form.is_valid():
        contexto['selection_error'] = form.non_field_errors()
        return render(request, 'chamados/resolver.html', contexto, status=400)
    ids = form.cleaned_data['ids']
    try:
        conferir_selecionados(equipamento_id=pk, ids=ids)
    except ConflitoSelecao:
        return render(request, 'chamados/resolver.html', {**contexto, 'conflict': True}, status=409)
    relatos = relatos_abertos(equipamento).filter(pk__in=ids)
    contexto.update({
        'selection_token': signing.dumps({'equipamento': pk, 'ids': ids}, salt=assinatura_da_sessao(request)),
        'columns': ['Relato', 'Problema', 'Descrição', 'Laboratório no envio', 'Aberto em'],
        'rows': [{'cells': [relato.pk, relato.problema.nome, relato.descricao or 'Sem descrição adicional',
                            relato.laboratorio.nome, timezone.localtime(relato.data_abertura)]} for relato in relatos],
    })
    return render(request, 'chamados/resolver.html', contexto)


@never_cache
@acesso_tecnico(alterar=True)
@require_POST
def resolver(request, pk):
    equipamento = equipamento_por_id(pk)
    contexto = {'equipamento': equipamento, 'backend_connected': True}
    try:
        selecao = signing.loads(request.POST.get('selection_token', ''), salt=assinatura_da_sessao(request))
        if selecao['equipamento'] != pk:
            raise signing.BadSignature
    except (signing.BadSignature, KeyError, TypeError):
        contexto['selection_error'] = ['Confira a seleção novamente antes de resolver']
        return render(request, 'chamados/resolver.html', contexto, status=400)
    try:
        quantidade = resolver_selecionados(usuario=request.user, equipamento_id=pk, ids=selecao['ids'])
    except ConflitoSelecao:
        return render(request, 'chamados/resolver.html', {**contexto, 'conflict': True}, status=409)
    messages.success(request, f'{quantidade} relatos resolvidos')
    if equipamento.chamados.filter(status=Chamado.ABERTO).exists():
        return redirect('paginas:relatos_equipamento', pk=pk)
    return redirect('paginas:painel')


@never_cache
@acesso_tecnico()
@require_GET
def contagem(request):
    dados = list(contagem_tecnica())
    rows = [{'cells': [linha['laboratorio__nome'], linha['equipamento__codigo_patrimonio'], linha['problema__nome'],
                       linha['abertos'], linha['resolvidos'], linha['total']]} for linha in dados]
    return render(request, 'chamados/contagem.html', {
        'rows': rows, 'columns': ['Laboratório no envio', 'Equipamento', 'Problema', 'Abertos', 'Resolvidos', 'Total'],
        'totals': [sum(linha[campo] for linha in dados) for campo in ('abertos', 'resolvidos', 'total')],
        'backend_connected': True,
    })
