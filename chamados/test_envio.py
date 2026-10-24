from unittest.mock import patch
from uuid import uuid4

from django.test import Client, TestCase
from django.urls import reverse

from equipamentos.models import Equipamento, Laboratorio, Local
from .models import Chamado, Tag
from .servicos import criar_relato


class EnvioTests(TestCase):
    def setUp(self):
        laboratorio = Laboratorio.objects.create(codigo='LAB', nome='Laboratório')
        local = Local.objects.create(laboratorio=laboratorio, nome='Bancada')
        self.equipamento = Equipamento.objects.create(nome='PC', codigo_patrimonio='PC-01', local=local)
        self.problema = Tag.objects.create(nome='Não liga')
        self.url = reverse('paginas:relato', args=[self.equipamento.qr_token])

    def test_formulario_real_tem_csrf_e_identificacao(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'PC-01')
        self.assertContains(resposta, 'csrfmiddlewaretoken')
        self.assertContains(resposta, 'type="submit"')
        self.assertNotContains(resposta, 'name="equipamento"')
        self.assertNotContains(resposta, 'name="laboratorio"')

    def test_envio_usa_equipamento_da_url_e_confirma_sem_dados(self):
        resposta = self.client.post(self.url, {
            'problema': self.problema.pk, 'descricao': '  conteúdo privado  ',
            'equipamento': 999, 'laboratorio': 999,
        })
        self.assertRedirects(resposta, reverse('paginas:confirmacao'))
        chamado = Chamado.objects.get()
        self.assertEqual(chamado.equipamento_id, self.equipamento.pk)
        self.assertEqual(chamado.laboratorio_id, self.equipamento.local.laboratorio_id)
        self.assertEqual(chamado.descricao, 'conteúdo privado')
        for _ in range(2):
            confirmacao = self.client.get(reverse('paginas:confirmacao'))
            self.assertNotContains(confirmacao, 'conteúdo privado')
            self.assertNotContains(confirmacao, 'PC-01')
        self.assertEqual(Chamado.objects.count(), 1)

    def test_descricao_opcional_e_regra_de_outro_por_identidade(self):
        self.assertEqual(self.client.post(self.url, {'problema': self.problema.pk}).status_code, 302)
        outro = Tag.objects.get(outro=True)
        outro.nome = 'Outra situação'
        outro.save()
        resposta = self.client.post(self.url, {'problema': outro.pk, 'descricao': '   '})
        self.assertContains(resposta, 'Descreva o problema para continuar')
        self.assertEqual(Chamado.objects.count(), 1)
        self.assertEqual(self.client.post(self.url, {'problema': outro.pk, 'descricao': 'x' * 250}).status_code, 302)

    def test_erros_preservam_texto_e_nao_criam_relato(self):
        for problema in ('', '999999', 'abc'):
            resposta = self.client.post(self.url, {'problema': problema, 'descricao': 'Texto para corrigir'})
            self.assertContains(resposta, 'Texto para corrigir')
        resposta = self.client.post(self.url, {'problema': self.problema.pk, 'descricao': 'x' * 251})
        self.assertContains(resposta, 'Use no máximo 250 caracteres')
        self.assertFalse(Chamado.objects.exists())

    def test_rejeita_campos_repetidos_e_escapa_texto(self):
        resposta = self.client.post(self.url, {'problema': [self.problema.pk, self.problema.pk], 'descricao': '<script>alert(1)</script>'})
        self.assertContains(resposta, 'Envie somente um valor por campo')
        self.assertNotContains(resposta, '<script>alert(1)</script>')
        self.assertFalse(Chamado.objects.exists())

    def test_equipamento_invalido_inativo_e_catalogo_vazio(self):
        self.assertEqual(self.client.get(reverse('paginas:relato', args=[uuid4()])).status_code, 404)
        self.equipamento.ativo = False
        self.equipamento.save()
        self.assertEqual(self.client.post(self.url, {'problema': self.problema.pk}).status_code, 403)
        self.equipamento.ativo = True
        self.equipamento.save()
        Tag.objects.all().delete()
        self.assertEqual(self.client.get(self.url).status_code, 503)
        self.assertFalse(Chamado.objects.exists())

    def test_desativacao_entre_validacao_e_gravacao(self):
        def desativar_e_criar(**dados):
            self.equipamento.ativo = False
            self.equipamento.save()
            return criar_relato(**dados)

        with patch('chamados.views.criar_relato', side_effect=desativar_e_criar):
            resposta = self.client.post(self.url, {'problema': self.problema.pk})
        self.assertContains(resposta, 'Não foi possível enviar o relato')
        self.assertFalse(Chamado.objects.exists())

    def test_csrf_obrigatorio_e_envio_com_token_valido(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(self.url, {'problema': self.problema.pk}).status_code, 403)
        cliente.get(self.url)
        resposta = cliente.post(self.url, {
            'problema': self.problema.pk, 'csrfmiddlewaretoken': cliente.cookies['csrftoken'].value,
        })
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Chamado.objects.count(), 1)
