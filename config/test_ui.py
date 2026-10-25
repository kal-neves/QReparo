from importlib import reload
from types import SimpleNamespace

from django import forms
from django.contrib.auth.context_processors import PermWrapper
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import clear_url_caches, resolve, Resolver404

from chamados.templatetags.ui import ui_control


def user_with(*permissions, staff=False):
    return SimpleNamespace(is_staff=staff, is_authenticated=True,
                           has_perm=lambda name: name in permissions)


class InterfaceTests(SimpleTestCase):
    def render_header(self, user, **context):
        request = RequestFactory().get('/')
        request.user = user
        return render_to_string('ui/header.html', {'user': user, 'perms': PermWrapper(user), **context}, request)

    def test_public_header_stays_public_for_technician(self):
        html = self.render_header(user_with('chamados.view_chamado', staff=True), internal=False)
        self.assertIn('Área técnica', html)
        self.assertNotIn('Contagem técnica', html)
        self.assertNotIn('Cadastros', html)
        self.assertNotIn('class="qr-brand" href=', html)

    def test_internal_navigation_respects_permissions_and_active_page(self):
        html = self.render_header(user_with('chamados.view_chamado'), internal=True, active_nav='painel')
        self.assertIn('aria-current="page"', html)
        self.assertIn('Contagem técnica', html)
        self.assertNotIn('Cadastros', html)
        self.assertIn('Sair', html)
        admin = self.render_header(user_with(staff=True), internal=True, logout_url='/sair/')
        self.assertIn('Cadastros', admin)
        self.assertNotIn('Contagem técnica', admin)
        self.assertIn('method="post" action="/sair/"', admin)
        self.assertIn('csrfmiddlewaretoken', admin)

    def test_field_errors_keep_accessible_associations_without_mutating_widget(self):
        class Example(forms.Form):
            nome = forms.CharField(help_text='Ajuda', widget=forms.TextInput(attrs={'class': 'original'}))
        form = Example({'nome': ''}, prefix='sample')
        widget = form.fields['nome'].widget
        before = widget.attrs.copy()
        html = render_to_string('ui/field.html', {'field': form['nome']})
        self.assertIn('for="id_sample-nome"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id_sample-nome_helptext id_sample-nome_errors', html)
        self.assertIn('id="id_sample-nome_errors"', html)
        self.assertEqual(widget.attrs, before)
        valid = Example({'nome': 'Texto'})
        self.assertNotIn('is-invalid', ui_control(valid['nome']))

    def test_components_escape_report_and_alert_content(self):
        payload = '<script>alert(1)</script>'
        html = render_to_string('ui/report_card.html', {
            'report_id': 1, 'problem': payload, 'description': payload + '\nSegunda linha',
        })
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('<br>', html)
        alert = render_to_string('ui/alert.html', {'text': payload, 'kind': 'danger'})
        self.assertNotIn('<script>', alert)
        self.assertIn('role="alert"', alert)

    def test_preview_route_is_absent_when_debug_is_false(self):
        import config.urls
        try:
            with override_settings(DEBUG=False):
                reload(config.urls)
                clear_url_caches()
                with self.assertRaises(Resolver404):
                    resolve('/_ui/')
            with override_settings(DEBUG=True):
                reload(config.urls)
                clear_url_caches()
                self.assertEqual(resolve('/_ui/').url_name, 'ui-preview')
        finally:
            reload(config.urls)
            clear_url_caches()
