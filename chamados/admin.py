from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Chamado


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    """
    Configuração do painel administrativo para a gestão de chamados no QReparo.
    """
    list_display = (
        'id_formatado',
        'titulo',
        'equipamento',
        'solicitante',
        'tecnico_responsavel',
        'prioridade_formatada',
        'status_formatado',
        'data_abertura',
    )
    list_filter = (
        'status',
        'prioridade',
        'data_abertura',
        'tecnico_responsavel',
        'equipamento__categoria',
    )
    search_fields = (
        'titulo',
        'descricao',
        'equipamento__nome',
        'equipamento__codigo_patrimonio',
        'solicitante__username',
        'solicitante__first_name',
        'solicitante__last_name',
        'laudo_tecnico',
    )
    ordering = ('-data_abertura',)
    list_per_page = 20

    raw_id_fields = ('equipamento', 'solicitante', 'tecnico_responsavel')
    readonly_fields = ('data_abertura', 'data_atualizacao', 'data_conclusao')

    fieldsets = (
        ('Identificação do Chamado', {
            'fields': ('titulo', 'equipamento', 'prioridade', 'status')
        }),
        ('Descrição do Problema', {
            'fields': ('descricao',)
        }),
        ('Atores Envolvidos', {
            'fields': ('solicitante', 'tecnico_responsavel')
        }),
        ('Atendimento e Resolução Técnica', {
            'fields': ('laudo_tecnico',)
        }),
        ('Controle de Datas e Conclusão', {
            'classes': ('collapse',),
            'fields': ('data_abertura', 'data_atualizacao', 'data_conclusao')
        }),
    )

    actions = ['marcar_como_resolvido', 'assumir_chamados']

    @admin.display(description='# ID', ordering='id')
    def id_formatado(self, obj):
        return f"#{obj.id}"

    @admin.display(description='Prioridade', ordering='prioridade')
    def prioridade_formatada(self, obj):
        cores = {
            'BAIXA': '#64748b',    # cinza
            'MEDIA': '#2563eb',    # azul
            'ALTA': '#d97706',     # âmbar
            'URGENTE': '#dc2626',  # vermelho
        }
        cor = cores.get(obj.prioridade, '#64748b')
        return format_html(
            '<span style="display:inline-block; padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: #ffffff; font-weight: 600; font-size: 11px;">{}</span>',
            cor,
            obj.get_prioridade_display()
        )

    @admin.display(description='Status', ordering='status')
    def status_formatado(self, obj):
        cores = {
            'ABERTO': '#dc2626',          # vermelho
            'EM_ATENDIMENTO': '#2563eb',  # azul
            'RESOLVIDO': '#16a34a',       # verde
            'CANCELADO': '#64748b',       # cinza
        }
        cor = cores.get(obj.status, '#64748b')
        return format_html(
            '<span style="display:inline-block; padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: #ffffff; font-weight: 600; font-size: 11px;">{}</span>',
            cor,
            obj.get_status_display()
        )

    @admin.action(description='Marcar chamados selecionados como RESOLVIDO')
    def marcar_como_resolvido(self, request, queryset):
        agora = timezone.now()
        for chamado in queryset:
            chamado.status = Chamado.STATUS_RESOLVIDO
            chamado.data_conclusao = agora
            if not chamado.laudo_tecnico:
                chamado.laudo_tecnico = f"Resolvido via ação em lote do Django Admin por {request.user.username}."
            chamado.save()
        self.message_user(request, f"{queryset.count()} chamado(s) finalizado(s) e marcado(s) como Resolvido.")

    @admin.action(description='Assumir chamados selecionados (Atribuir a mim)')
    def assumir_chamados(self, request, queryset):
        atualizados = queryset.update(
            tecnico_responsavel=request.user,
            status=Chamado.STATUS_EM_ATENDIMENTO
        )
        self.message_user(request, f"{atualizados} chamado(s) atribuído(s) a {request.user.username}.")
