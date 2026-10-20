from django import template
from django.forms import CheckboxInput, Select

register = template.Library()


@register.filter
def ui_control(field):
    """Estiliza BoundField sem alterar o widget compartilhado entre renderizações."""
    widget = field.field.widget
    css = 'form-check-input' if isinstance(widget, CheckboxInput) else 'form-select' if isinstance(widget, Select) else 'form-control'
    attrs = {'class': f"{widget.attrs.get('class', '')} {css}".strip()}
    described = widget.attrs.get('aria-describedby', '').split()
    if field.help_text:
        described.append(f'{field.auto_id}_helptext')
    if field.errors:
        attrs['class'] += ' is-invalid'
        attrs['aria-invalid'] = 'true'
        described.append(f'{field.auto_id}_errors')
    if described:
        attrs['aria-describedby'] = ' '.join(dict.fromkeys(described))
    return field.as_widget(attrs=attrs)
