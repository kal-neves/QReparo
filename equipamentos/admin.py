from django.contrib import admin
from .models import Equipamento, Laboratorio, Local


@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome')
    search_fields = ('codigo', 'nome')


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'laboratorio')
    list_filter = ('laboratorio',)


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo_patrimonio', 'nome', 'local', 'ativo')
    list_filter = ('ativo', 'local__laboratorio')
    search_fields = ('codigo_patrimonio', 'nome')
    readonly_fields = ('qr_token',)
    list_select_related = ('local__laboratorio',)
    # Sem inline de relatos ou ações de atendimento. Contas de cadastro não
    # recebem acesso aos relatos automaticamente.
