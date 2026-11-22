"""Dados fictícios do catálogo; sem consultas ou mutações de modelos."""
from django import forms
from django.core.paginator import Paginator


TAGS = [(str(i), label) for i, label in enumerate([
    'Não liga', 'Sem internet', 'Lentidão', 'Periférico', 'Software',
    'Monitor', 'Teclado/mouse', 'Áudio', 'Impressora', 'Outro problema'])]


class ComponentsForm(forms.Form):
    tags = forms.MultipleChoiceField(label='Problemas', choices=TAGS,
        widget=forms.CheckboxSelectMultiple)
    foto = forms.FileField(label='Foto 1', required=False,
        help_text='PNG, JPEG ou HEIC, até 10 MB. A demonstração não envia arquivos.',
        widget=forms.FileInput(attrs={'accept': 'image/png,image/jpeg,image/heic,.png,.jpg,.jpeg,.heic'}))
    prioridade = forms.ChoiceField(label='Prioridade', choices=[(x, x) for x in ['Baixa', 'Média', 'Alta', 'Crítica']])
    responsavel = forms.ChoiceField(label='Responsável', required=False,
        choices=[('', 'Sem responsável'), ('exemplo', 'Técnico de exemplo')])
    nota = forms.CharField(label='Nota interna', widget=forms.Textarea, required=False)


class FilterForm(forms.Form):
    busca = forms.CharField(label='Buscar equipamento', required=False)
    estado = forms.ChoiceField(label='Estado', required=False,
        choices=[('', 'Todos'), ('Aberto', 'Aberto'), ('Resolvido', 'Resolvido')])
    inicio = forms.DateField(label='Abertura a partir de', required=False,
        widget=forms.DateInput(attrs={'type': 'date'}))


def components_context(request):
    form = FilterForm(request.GET or None, auto_id='filter_%s')
    valid = form.is_bound and form.is_valid()
    fixtures = [{'id': i, 'name': f'PC-{i:02}', 'state': 'Aberto' if i % 2 else 'Resolvido',
                 'opened': '2026-11-03'} for i in range(1, 9)]
    if valid:
        data = form.cleaned_data
        fixtures = [row for row in fixtures
                    if data['busca'].casefold() in row['name'].casefold()
                    and (not data['estado'] or row['state'] == data['estado'])
                    and (not data['inicio'] or row['opened'] >= data['inicio'].isoformat())]
    page = Paginator(fixtures, 3).get_page(request.GET.get('page'))
    return {
        'components_form': ComponentsForm(prefix='components'),
        'filter_form': form, 'demo_page': page, 'demo_query': request.GET,
        'demo_rows': [{'cells': [r['name'], r['state'], '03/11/2026']} for r in page],
        'demo_columns': ['Equipamento fictício', 'Estado', 'Abertura'],
        'states': [('Aberto', ''), ('Em atendimento', 'info'), ('Pendente', 'warning'),
                   ('Resolvido', 'success'), ('Cancelado', 'danger')],
        'priorities': [('Baixa', ''), ('Média', 'warning'), ('Alta', 'danger'), ('Crítica', 'danger')],
        'navigation_demo': [{'key': key, 'label': label, 'url': '#' + target} for key, label, target in [
            ('chamados', 'Chamados', 'full-reports'), ('equipamentos', 'Equipamentos', 'full-filters'),
            ('restricoes', 'Restrições', 'full-history'), ('indicadores', 'Indicadores', 'full-metrics')]],
        'metadata_demo': [{'label': 'Responsável', 'value': 'Sem responsável'},
                          {'label': 'Primeiro atendimento', 'value': None},
                          {'label': 'Laboratório no envio', 'value': 'Laboratório de exemplo'}],
        'history_columns': ['Autor', 'Data e hora', 'Alteração'],
        'history_rows': [{'cells': ['Técnico de exemplo', '03/11/2026 10:00', 'Aberto → Em atendimento']},
                         {'cells': ['Técnico de exemplo', '03/11/2026 10:05', 'Prioridade: Média → Alta']}],
        'photo_demo': [{'label': 'Abrir ilustração de exemplo', 'url': '/static/brand/QReparo_logo_noSign_horizontal.svg',
                        'thumbnail': '/static/brand/QReparo_logo_noSign_horizontal.svg',
                        'caption': 'Marca pública usada como demonstração, sem foto privada.'},
                       {'label': 'Foto removida', 'url': ''}],
    }
