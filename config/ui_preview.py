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
    if request.GET.get('tela') == 'relatos':
        estado = request.GET.get('estado', '')
        reports = [
            {'id': 101, 'problem': 'Não liga', 'opened_at': '09/10/2026 09:15',
             'laboratory': 'Lab. 01 — Informática', 'description': 'O computador não liga, mesmo conectado à tomada.'},
            {'id': 102, 'problem': 'Teclado/mouse', 'opened_at': '10/10/2026 10:30',
             'laboratory': 'Lab. 01 — Informática', 'description': ''},
            {'id': 103, 'problem': 'Outro problema', 'opened_at': '11/10/2026 14:00',
             'laboratory': 'Lab. 02 — Multimídia', 'description': 'O computador faz um barulho estranho.\nO ruído aparece ao ligar.'},
        ]
        return render(request, 'chamados/detalhe.html', {
            'equipamento': {'codigo_patrimonio': 'PC-01', 'nome': 'Computador Lenovo',
                'descricao': 'Computador de uso acadêmico',
                'local': {'nome': 'Bancada A · Posição 01',
                          'laboratorio': {'nome': 'Laboratório 01 — Informática'}}},
            'reports': [] if estado == 'vazio' else reports[2:] if estado == 'parcial' else reports,
            'equipment_inactive': estado == 'inativo',
            'resolved_count': 2 if estado == 'parcial' else 0,
            'resolution_message': '2 relatos resolvidos.',
            'perms': {'chamados': {'view_chamado': True}}, 'user': {'is_staff': True},
        })
    if request.GET.get('tela') == 'painel':
        # Dados fixos para composição visual; não consultam equipamento ou chamado.
        rows = [
            {'cells': ['PC-01', 'Lab. 01 — Informática', 'Bancada A · Posição 01', 3], 'description': 'Computador Lenovo', 'icon': 'monitor', 'action_label': 'Ver relatos'},
            {'cells': ['PC-12', 'Lab. 01 — Informática', 'Bancada B · Posição 02', 4], 'description': 'Computador Dell', 'icon': 'monitor', 'action_label': 'Ver relatos'},
            {'cells': ['PRJ-03', 'Lab. 02 — Multimídia', 'Teto · Centro', 2], 'description': 'Projetor Epson', 'icon': 'monitor', 'action_label': 'Ver relatos'},
            {'cells': ['IMP-01', 'Lab. 03 — Informática', 'Mesa de apoio', 5], 'description': 'Impressora HP', 'icon': 'print', 'action_label': 'Ver relatos'},
            {'cells': ['AC-02', 'Lab. 04 — Redes', 'Parede lateral', 1], 'description': 'Ar-condicionado', 'icon': 'monitor', 'action_label': 'Ver relatos'},
            {'cells': ['MIC-01', 'Lab. 05 — Biologia', 'Bancada 01', 1], 'description': 'Microscópio', 'icon': 'lab', 'action_label': 'Ver relatos'},
        ]
        return render(request, 'chamados/painel.html', {
            'rows': [] if request.GET.get('estado') == 'vazio' else rows,
            'columns': ['Equipamento', 'Laboratório', 'Localização', 'Relatos abertos'],
            'perms': {'chamados': {'view_chamado': True}},
            'user': {'is_staff': request.GET.get('perfil') != 'tecnico'},
        })
    if request.GET.get('tela') == 'entrada':
        estado = request.GET.get('estado', '')
        return render(request, 'registration/login.html', {
            'login_error': estado == 'erro', 'session_expired': estado == 'expirada',
            'username': 'tecnico.exemplo' if estado == 'erro' else '',
        })
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
