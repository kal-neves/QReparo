from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse


class AcessoTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user('tecnico', password='senha-de-teste')
        self.usuario.user_permissions.add(Permission.objects.get(codename='view_chamado'))
        self.entrada = reverse('paginas:entrada')

    def entrar(self, **dados):
        return self.client.post(self.entrada, {'username': 'tecnico', 'password': 'senha-de-teste', **dados})

    def test_login_logout_e_protecao_das_paginas(self):
        for nome in ('painel', 'contagem'):
            resposta = self.client.get(reverse(f'paginas:{nome}'))
            self.assertEqual(resposta.status_code, 302)
            self.assertTrue(resposta.url.startswith(self.entrada))
        self.assertRedirects(self.entrar(), reverse('paginas:painel'))
        saida = reverse('paginas:saida')
        self.assertEqual(self.client.get(saida).status_code, 405)
        self.assertRedirects(self.client.post(saida), self.entrada)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_destino_seguro_e_autorizado(self):
        for destino in ('https://outro.example', '/tecnico/equipamentos/1/conferencia/', '/admin/'):
            self.assertRedirects(self.entrar(next=destino), reverse('paginas:painel'))
        self.assertRedirects(self.entrar(next='/tecnico/contagem/'), '/tecnico/contagem/')

    def test_credenciais_invalidas_e_inativo_tem_mesmo_erro(self):
        resposta = self.entrar(password='senha-errada')
        self.assertContains(resposta, 'Não foi possível entrar')
        self.assertContains(resposta, 'value="tecnico"')
        self.assertNotContains(resposta, 'value="senha-errada"')
        self.usuario.is_active = False
        self.usuario.save()
        self.assertContains(self.entrar(), 'Não foi possível entrar')

    def test_staff_nao_ganha_acesso_aos_relatos(self):
        self.usuario.user_permissions.clear()
        self.usuario.is_staff = True
        self.usuario.save()
        self.assertRedirects(self.entrar(), reverse('admin:index'))
        self.assertEqual(self.client.get('/tecnico/').status_code, 403)
        self.assertEqual(self.client.get('/chamados/api/').status_code, 403)
        self.assertRedirects(self.client.get('/'), reverse('admin:index'))

    def test_conta_sem_permissoes_recebe_acesso_negado(self):
        self.usuario.user_permissions.clear()
        self.assertEqual(self.entrar().status_code, 403)
        self.assertEqual(self.client.get('/').status_code, 403)

    def test_csrf_no_login_e_logout(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(self.entrada, {'username': 'tecnico', 'password': 'senha-de-teste'}).status_code, 403)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(reverse('paginas:saida')).status_code, 403)

    def test_login_preserva_origem_e_recusa_origens_invalidas(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.get(self.entrada)
        self.assertEqual(resposta['Referrer-Policy'], 'same-origin')
        dados = {
            'username': 'tecnico', 'password': 'senha-de-teste',
            'csrfmiddlewaretoken': cliente.cookies['csrftoken'].value,
        }
        for origem in ('null', 'http://outro.example'):
            with self.subTest(origem=origem):
                resposta = cliente.post(self.entrada, dados, HTTP_ORIGIN=origem)
                self.assertEqual(resposta.status_code, 403)
                self.assertNotIn('_auth_user_id', cliente.session)
        resposta = cliente.post(self.entrada, dados, HTTP_ORIGIN='http://testserver')
        self.assertRedirects(resposta, reverse('paginas:painel'))
        self.assertEqual(cliente.session['_auth_user_id'], str(self.usuario.pk))
