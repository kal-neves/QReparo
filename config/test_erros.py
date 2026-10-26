from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils.functional import SimpleLazyObject

from .erros import erro_interno


class ErroInternoTests(SimpleTestCase):
    def test_500_funciona_sem_usuario_sessao_ou_banco(self):
        def indisponivel():
            raise RuntimeError('banco indisponivel')

        request = RequestFactory().get('/tecnico/')
        request.user = SimpleLazyObject(indisponivel)
        request.session = SimpleLazyObject(indisponivel)
        request._messages = SimpleLazyObject(indisponivel)
        resposta = erro_interno(request)
        self.assertContains(resposta, 'Não foi possível concluir', status_code=500)
        self.assertContains(resposta, 'Consulte o estado atual dos relatos', status_code=500)
        self.assertNotContains(resposta, 'banco indisponivel', status_code=500)
        self.assertNotContains(resposta, 'Contagem técnica', status_code=500)
        self.assertIn('no-store', resposta['Cache-Control'])


@override_settings(DEBUG=False)
class ErrosTests(TestCase):
    def test_404_nao_reflete_url_e_403_nao_mostra_area_tecnica(self):
        resposta = self.client.get('/conteudo-privado-inexistente/')
        self.assertContains(resposta, 'Página não encontrada', status_code=404)
        self.assertNotContains(resposta, 'conteudo-privado-inexistente', status_code=404)
        usuario = get_user_model().objects.create_user('sem-permissao')
        self.client.force_login(usuario)
        resposta = self.client.get('/tecnico/')
        self.assertContains(resposta, 'Acesso não permitido', status_code=403)
        self.assertNotContains(resposta, 'Contagem técnica', status_code=403)

    def test_csrf_nao_expoe_conteudo_e_500_nao_expoe_excecao(self):
        cliente = Client(enforce_csrf_checks=True, raise_request_exception=False)
        resposta = cliente.post('/entrar/', {'password': 'segredo-enviado'})
        self.assertContains(resposta, 'Abra o formulário novamente', status_code=403)
        self.assertNotContains(resposta, 'segredo-enviado', status_code=403)
        with patch('config.paginas.redirect', side_effect=RuntimeError('detalhe-privado')):
            resposta = cliente.get('/')
        self.assertContains(resposta, 'Não foi possível concluir', status_code=500)
        self.assertNotContains(resposta, 'detalhe-privado', status_code=500)
        self.assertIn('no-store', resposta['Cache-Control'])
