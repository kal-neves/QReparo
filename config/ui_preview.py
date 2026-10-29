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


# Fixtures de apresentação: nenhum dado abaixo vem de modelos ou de envios.
def remaining_preview(request, screen):
    state = request.GET.get('estado', '')
    technical = request.GET.get('perfil') == 'tecnico'
    navigation = {'perms': {'chamados': {'view_chamado': True}}, 'user': {'is_staff': True}}
    equipment = {'codigo_patrimonio': 'PC-01', 'nome': 'Computador Lenovo',
                 'descricao': 'Computador de uso acadêmico',
                 'local': {'nome': 'Bancada A · Posição 01',
                           'laboratorio': {'nome': 'Laboratório 01 — Informática'}}}
    if screen == 'conferencia':
        rows = [
            {'cells': ['101', 'Não liga', 'O computador não liga, mesmo conectado à tomada.\nA luz de energia permanece apagada.', 'Lab. 01 — Informática', '09/10/2026 09:15']},
            {'cells': ['102', 'Teclado/mouse', 'Sem descrição adicional', 'Lab. 01 — Informática', '10/10/2026 10:30']},
        ]
        return render(request, 'chamados/resolver.html', {
            **navigation, 'equipamento': equipment,
            'rows': [] if state in ('vazio', 'conflito', 'falha') else rows[:1] if state == 'unico' else rows,
            'columns': ['Relato', 'Problema', 'Descrição', 'Laboratório no envio', 'Aberto em'],
            'conflict': state == 'conflito', 'affected_reports': ['101'] if state == 'conflito' else [],
            'uncertain_result': state == 'falha',
        })
    if screen == 'contagem':
        rows = [
            {'cells': ['Lab. 01 — Informática', 'PC-01', 'Não liga', 1, 2, 3]},
            {'cells': ['Lab. 01 — Informática', 'PC-01', 'Outro problema', 1, 0, 1]},
            {'cells': ['Lab. 01 — Informática', 'PC-01', 'Teclado/mouse', 1, 1, 2]},
            {'cells': ['Lab. 01 — Informática', 'PC-12', 'Lentidão', 4, 2, 6]},
            {'cells': ['Lab. 02 — Multimídia', 'PRJ-03', 'Monitor', 2, 1, 3]},
            {'cells': ['Lab. 03 — Informática', 'IMP-01', 'Impressora', 5, 3, 8]},
            {'cells': ['Lab. 04 — Redes', 'AC-02', 'Outro problema', 1, 0, 1]},
            {'cells': ['Lab. 05 — Biologia', 'MIC-01', 'Outro problema', 1, 1, 2]},
        ]
        return render(request, 'chamados/contagem.html', {
            **navigation, 'rows': [] if state == 'vazio' else rows, 'totals': [16, 10, 26],
            'columns': ['Laboratório no envio', 'Equipamento', 'Problema', 'Abertos', 'Resolvidos', 'Total'],
        })
    states = {
        'acesso': {'state_title': 'Acesso não permitido',
                   'state_text': 'Sua conta não tem permissão para acessar esta página.',
                   'state_icon': 'lock', 'minimal_header': True, 'show_exit': True, 'technical': True},
        'pagina': {'state_title': 'Página não encontrada',
                   'state_text': 'Não encontramos a página que você tentou acessar.',
                   'state_icon': 'file-question',
                   'action_label': 'Voltar aos equipamentos' if technical else None},
        'formulario': {'state_title': 'Não foi possível enviar',
                       'state_text': 'Abra o formulário novamente e tente de novo.',
                       'state_icon': 'clock', 'action_label': 'Abrir formulário novamente', 'technical': False},
        'interno': {'state_title': 'Não foi possível concluir',
                    'state_text': 'Tente novamente mais tarde.', 'state_icon': 'warning', 'minimal_header': True,
                    'state_detail': 'Consulte o estado atual dos relatos antes de repetir a operação.' if technical else ''},
        'equipamento': {'state_title': 'Equipamento não encontrado',
                        'state_text': 'Confira se você escaneou a etiqueta correta.', 'state_icon': 'monitor', 'technical': False},
        'inativo': {'state_title': 'Equipamento indisponível',
                    'state_text': 'Este equipamento não está recebendo novos relatos.', 'state_icon': 'monitor', 'technical': False},
    }
    return render(request, 'paginas/estado.html', {
        **navigation, 'technical': technical, **states.get(state, states['pagina']),
    })


@require_safe
def preview(request):
    if request.GET.get('tela') in ('conferencia', 'contagem', 'erro'):
        return remaining_preview(request, request.GET['tela'])
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
