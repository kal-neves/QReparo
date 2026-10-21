"""Exemplos visuais, disponíveis somente quando DEBUG está ativo."""
from django import forms
from django.forms.utils import ErrorDict, ErrorList
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.http import require_safe


class ExampleForm(forms.Form):
    problema = forms.ChoiceField(label='Problema', choices=[('', 'Selecione um problema'), ('exemplo', 'Problema de exemplo')])
    descricao = forms.CharField(label='Descrição', required=False, max_length=250,
        help_text='Não inclua nome, matrícula, contato ou outros dados pessoais.',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva brevemente o que aconteceu.'}))


class ReportPreviewForm(forms.Form):
    """Somente apresentação de campos fictícios; não recebe nem salva envios."""
    problema = forms.ChoiceField(label='Problema', choices=[
        ('', 'Selecione um problema'), ('ligar', 'Não liga'),
        ('rede', 'Sem conexão com a rede'), ('lento', 'Lentidão'), ('outro', 'Outro problema'),
    ])
    descricao = forms.CharField(label='Descrição', required=False, max_length=250,
        help_text='Obrigatória para “Outro problema”. Não inclua nome, matrícula, contato ou outros dados pessoais.',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ex.: a rede cai a cada cinco minutos'}))


def report_preview(request):
    estado = request.GET.get('estado', '')
    form = ReportPreviewForm(initial={'problema': 'outro' if estado == 'outro' else ''})
    # Erros fixos para inspecionar o componente; nenhuma validação de requisição.
    errors = {
        'erro': ('problema', 'Selecione um problema.'),
        'outro': ('descricao', 'Descreva o problema para continuar.'),
        'limite': ('descricao', 'Use no máximo 250 caracteres.'),
    }
    if estado in errors:
        field, message = errors[estado]
        form._errors = ErrorDict({field: ErrorList([message])})
    return render(request, 'chamados/novo.html', {
        'titulo': 'Registrar problema', 'preview_visual': True,
        'internal': False, 'desktop': False, 'form': form,
        'estado_visual': estado,
        'equipamento': {'codigo_patrimonio': 'PC-01', 'nome': 'Computador Lenovo',
            'descricao': 'Computador de uso acadêmico',
            'local': {'nome': 'Bancada A · Posição 01',
                      'laboratorio': {'nome': 'Laboratório 01 — Informática'}}},
    })


@require_safe
def preview(request):
    if request.GET.get('tela') == 'relato':
        return report_preview(request)
    if request.GET.get('tela') == 'etiqueta':
        return render(request, 'equipamentos/etiqueta.html', {
            'titulo': 'Etiqueta do equipamento', 'internal': True, 'desktop': True,
            'active_nav': 'cadastros', 'preview_visual': True,
            'equipamento': {
                'codigo_patrimonio': 'PC-01', 'nome': 'Computador Lenovo',
                'ativo': request.GET.get('estado') != 'inativo',
                'local': {'nome': 'Bancada A · Posição 01',
                          'laboratorio': {'nome': 'Laboratório 01 — Informática'}},
            },
            'qr_image': static('img/qr-exemplo.png'),
        })
    invalid = ExampleForm({'problema': '', 'descricao': ''}, prefix='invalid')
    invalid.is_valid()
    return render(request, 'ui/catalogo.html', {
        'titulo': 'Componentes de interface',
        'example_form': ExampleForm(prefix='example'),
        'invalid_form': invalid,
        'columns': ['Equipamento', 'Laboratório', 'Localização', 'Relatos abertos'],
        'rows': [{'cells': ['PC-01', 'Laboratório 01', 'Bancada A · Posição 01', '3']},
                 {'cells': ['PC-02', 'Laboratório 01', 'Bancada A · Posição 02', '1']}],
    })
