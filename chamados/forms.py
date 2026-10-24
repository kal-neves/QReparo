from django import forms

from .models import Tag


class RelatoForm(forms.Form):
    problema = forms.ModelChoiceField(
        label='Problema', queryset=Tag.objects.all(), empty_label='Selecione um problema',
        error_messages={'required': 'Selecione um problema', 'invalid_choice': 'Selecione um problema válido'},
    )
    descricao = forms.CharField(
        label='Descrição', required=False, max_length=250,
        help_text='Obrigatória para “Outro problema” Não inclua nome, matrícula, contato ou outros dados pessoais',
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ex: a rede cai a cada cinco minutos'}),
        error_messages={'max_length': 'Use no máximo 250 caracteres'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        outro_id = Tag.objects.filter(outro=True).values_list('pk', flat=True).first()
        self.fields['problema'].widget.attrs['data-outro-id'] = str(outro_id or '')

    def clean(self):
        dados = super().clean()
        if hasattr(self.data, 'getlist'):
            for campo in ('problema', 'descricao'):
                if len(self.data.getlist(campo)) > 1:
                    self.add_error(campo, 'Envie somente um valor por campo')
        problema = dados.get('problema')
        if problema and problema.outro and not dados.get('descricao'):
            self.add_error('descricao', 'Descreva o problema para continuar')
        return dados
