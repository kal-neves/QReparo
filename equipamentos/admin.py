from django.contrib import admin
from django.utils.html import format_html
from .models import Equipamento
from chamados.models import Chamado


class ChamadoInline(admin.TabularInline):
    """
    Permite visualizar os chamados associados diretamente na tela
    de edição do Equipamento.
    """
    model = Chamado
    extra = 0
    fields = ('id', 'titulo', 'solicitante', 'tecnico_responsavel', 'prioridade', 'status', 'data_abertura')
    readonly_fields = ('id', 'titulo', 'solicitante', 'tecnico_responsavel', 'prioridade', 'status', 'data_abertura')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    """
    Configuração do painel administrativo para o inventário de equipamentos acadêmicos.
    """
    list_display = (
        'codigo_patrimonio',
        'nome',
        'categoria',
        'localizacao',
        'status_formatado',
        'chamados_pendentes',
        'criado_em'
    )
    list_filter = (
        'status',
        'categoria',
        'localizacao',
        'criado_em'
    )
    search_fields = (
        'nome',
        'codigo_patrimonio',
        'localizacao',
        'descricao'
    )
    ordering = (
        'nome',
        'codigo_patrimonio'
    )
    list_per_page = 25
    inlines = [ChamadoInline]

    fieldsets = (
        ('Identificação do Patrimônio', {
            'fields': ('nome', 'codigo_patrimonio', 'categoria')
        }),
        ('Localização e Estado', {
            'fields': ('localizacao', 'status', 'descricao')
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('criado_em', 'atualizado_em')
        }),
    )
    readonly_fields = ('criado_em', 'atualizado_em')

    actions = ['marcar_como_operacional', 'colocar_em_manutencao']

    @admin.display(description='Status', ordering='status')
    def status_formatado(self, obj):
        cores = {
            'OPERACIONAL': '#16a34a', # verde
            'MANUTENCAO': '#ea580c',  # laranja
            'INOPERANTE': '#dc2626',  # vermelho
        }
        cor = cores.get(obj.status, '#475569')
        return format_html(
            '<span style="display:inline-block; padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: #ffffff; font-weight: 600; font-size: 11px;">{}</span>',
            cor,
            obj.get_status_display()
        )

    @admin.display(description='Chamados Pendentes')
    def chamados_pendentes(self, obj):
        total = obj.total_chamados_abertos
        if total > 0:
            return format_html('<b style="color: #dc2626;">{} aberto(s)</b>', total)
        return format_html('<span style="color: #16a34a;">0</span>')

    @admin.action(description='Marcar equipamentos selecionados como OPERACIONAL')
    def marcar_como_operacional(self, request, queryset):
        atualizados = queryset.update(status=Equipamento.STATUS_OPERACIONAL)
        self.message_user(request, f"{atualizados} equipamento(s) marcado(s) como Operacional com sucesso.")

    @admin.action(description='Colocar equipamentos selecionados em MANUTENÇÃO')
    def colocar_em_manutencao(self, request, queryset):
        atualizados = queryset.update(status=Equipamento.STATUS_MANUTENCAO)
        self.message_user(request, f"{atualizados} equipamento(s) colocado(s) em Manutenção.")
