from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from .models import Equipamento, Laboratorio, Local


class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = '__all__'
        labels = {'codigo_patrimonio': 'Identificação'}
        help_texts = {'codigo_patrimonio': 'Use um código interno único, mesmo sem patrimônio institucional'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = True
        self.fields['categoria'].required = True


@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome')
    search_fields = ('codigo', 'nome')


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'laboratorio')
    list_filter = ('laboratorio',)

    def get_readonly_fields(self, request, obj=None):
        return ('laboratorio',) if obj else ()


@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    form = EquipamentoForm
    list_display = ('codigo_patrimonio', 'nome', 'categoria', 'local', 'ativo')
    list_filter = ('ativo', 'categoria', 'local__laboratorio')
    search_fields = ('codigo_patrimonio', 'nome', 'categoria')
    readonly_fields = ('qr_token', 'etiqueta')
    list_select_related = ('local__laboratorio',)

    @admin.display(description='Etiqueta')
    def etiqueta(self, obj):
        if not obj.pk:
            return 'Salve o equipamento para gerar a etiqueta'
        return format_html('<a href="{}">Ver etiqueta</a>', reverse('paginas:etiqueta', args=[obj.pk]))

    # Sem inline de relatos ou ações de atendimento. Contas de cadastro não
    # recebem acesso aos relatos automaticamente.
