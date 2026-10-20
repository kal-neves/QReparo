"""Exemplos visuais, disponíveis somente quando DEBUG está ativo."""
from django import forms
from django.shortcuts import render
from django.views.decorators.http import require_safe


class ExampleForm(forms.Form):
    problema = forms.ChoiceField(label='Problema', choices=[('', 'Selecione um problema'), ('exemplo', 'Problema de exemplo')])
    descricao = forms.CharField(label='Descrição', required=False, max_length=250,
        help_text='Não inclua nome, matrícula, contato ou outros dados pessoais.',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva brevemente o que aconteceu.'}))


@require_safe
def preview(request):
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
