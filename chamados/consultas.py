from django.db.models import Count, Q

from equipamentos.models import Equipamento
from .models import Chamado


def equipamentos_com_abertos():
    return (
        Equipamento.objects.select_related('local__laboratorio')
        .annotate(abertos=Count('chamados', filter=Q(chamados__status=Chamado.ABERTO)))
        .filter(abertos__gt=0)
        .order_by('local__laboratorio__nome', 'local__nome', 'codigo_patrimonio', 'pk')
    )


def relatos_abertos(equipamento):
    return (
        equipamento.chamados.filter(status=Chamado.ABERTO)
        .select_related('problema', 'laboratorio').order_by('data_abertura', 'pk')
    )


def contagem_tecnica():
    return (
        Chamado.objects.values(
            'laboratorio_id', 'laboratorio__nome', 'equipamento_id',
            'equipamento__codigo_patrimonio', 'problema_id', 'problema__nome',
        )
        .annotate(
            abertos=Count('pk', filter=Q(status=Chamado.ABERTO)),
            resolvidos=Count('pk', filter=Q(status=Chamado.RESOLVIDO)),
            total=Count('pk'),
        )
        .order_by('laboratorio__nome', 'equipamento__codigo_patrimonio', 'problema__nome')
    )
