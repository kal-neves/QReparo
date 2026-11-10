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
        self.assertNotIn('Área técnica', html)
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


class RemainingPreviewTests(SimpleTestCase):
    def render_preview(self, screen, state='', **params):
        from .ui_preview import preview
        request = RequestFactory().get('/_ui/', {'tela': screen, 'estado': state, **params})
        return preview(request)

    def test_preview_states_render_without_database_or_mutating_forms(self):
        cases = {
            'conferencia': ('', 'unico', 'conflito', 'falha', 'vazio'),
            'contagem': ('', 'vazio'),
            'erro': ('acesso', 'pagina', 'formulario', 'interno', 'equipamento', 'inativo'),
        }
        for screen, states in cases.items():
            for state in states:
                with self.subTest(screen=screen, state=state):
                    response = self.render_preview(screen, state)
                    self.assertEqual(response.status_code, 200)
                    self.assertNotContains(response, '<form')
                    self.assertNotContains(response, 'name="selection_token"')
        from .ui_preview import preview
        response = preview(RequestFactory().post('/_ui/?tela=conferencia'))
        self.assertEqual(response.status_code, 405)

    def test_review_exception_states_do_not_show_descriptions_or_confirmation(self):
        for state in ('conflito', 'falha', 'vazio'):
            with self.subTest(state=state):
                response = self.render_preview('conferencia', state)
                self.assertNotContains(response, 'A luz de energia permanece apagada.')
                self.assertNotContains(response, 'Confirmar resolução de')
        response = self.render_preview('conferencia', 'unico')
        self.assertContains(response, 'Confirmar resolução de 1 relato')
        self.assertNotContains(response, 'Teclado/mouse')

    def test_counts_and_error_variants(self):
        self.assertContains(self.render_preview('contagem'), 'Total geral')
        self.assertNotContains(self.render_preview('contagem', 'vazio'), '<table')
        for state in ('pagina', 'interno'):
            self.assertContains(self.render_preview('erro', state), 'class="qr-public"')
            self.assertContains(self.render_preview('erro', state, perfil='tecnico'), 'class="qr-desktop"')
        self.assertContains(self.render_preview('erro', 'desconhecido'), 'Página não encontrada')


class FullComponentsTests(SimpleTestCase):
    def catalog(self, params=None):
        from .ui_preview import preview
        return preview(RequestFactory().get('/_ui/', params or {}))

    def test_catalog_filters_paginate_fixtures_without_database(self):
        self.assertContains(self.catalog(), 'Página 1 de 3')
        self.assertContains(self.catalog({'estado': 'Resolvido'}), '4 resultados')
        self.assertContains(self.catalog({'busca': 'PC-08'}), '1 resultados')
        self.assertContains(self.catalog({'busca': 'ausente'}), 'Nenhum exemplo corresponde')
        self.assertContains(self.catalog({'inicio': 'invalida'}), 'invalid-feedback')
        self.assertContains(self.catalog({'page': '999'}), 'Página 3 de 3')

    def test_pagination_preserves_multivalued_filters_without_mutating_query(self):
        from django.core.paginator import Paginator
        from django.http import QueryDict
        from chamados.templatetags.ui import ui_pagination
        query = QueryDict('tag=1&tag=2&busca=a%26b&page=1')
        original = query.urlencode()
        context = ui_pagination(Paginator(range(6), 2).page(1), query)
        self.assertEqual(context['previous_url'], '')
        self.assertIn('tag=1&tag=2', context['next_url'])
        self.assertIn('page=2', context['next_url'])
        self.assertEqual(query.urlencode(), original)

    def test_metric_distinguishes_zero_from_unavailable(self):
        zero = render_to_string('ui/metric_card.html', {'label': 'Total', 'value': 0})
        unavailable = render_to_string('ui/metric_card.html', {'label': 'Tempo', 'value': None, 'unit': 'h'})
        self.assertIn('<dd>0</dd>', zero)
        self.assertIn('Indisponível', unavailable)
        self.assertNotIn('<span>h</span>', unavailable)

    def test_tag_selector_retains_bound_choices_errors_and_unique_ids(self):
        from .ui_components import ComponentsForm
        form = ComponentsForm({'a-tags': ['0', 'unknown']}, prefix='a')
        html = render_to_string('ui/tag_selector.html', {'field': form['tags']})
        self.assertRegex(html, r'value="0"[^>]* checked')
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('id_a-tags_errors', html)
        self.assertIn('for="id_a-tags_0"', html)

    def test_public_header_ignores_custom_internal_navigation(self):
        html = render_to_string('ui/header.html', {'internal': False,
            'navigation_items': [{'key': 'private', 'label': 'Segredo', 'url': '/privado/'}]})
        self.assertNotIn('Segredo', html)

    def test_new_components_escape_untrusted_text(self):
        payload = '<script>alert(1)</script>'
        for template, context in [
            ('metadata', {'items': [{'label': 'Nota', 'value': payload}]}),
            ('photo_list', {'photos': [{'label': payload}]}),
            ('metric_card', {'label': payload, 'value': 0}),
        ]:
            html = render_to_string(f'ui/{template}.html', context)
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)
