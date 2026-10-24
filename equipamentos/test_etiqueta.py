import base64
from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Equipamento, Laboratorio, Local
from .servicos import gerar_qr, url_do_relato


@override_settings(QREPARO_PUBLIC_URL='https://qreparo.example')
class EtiquetaTests(TestCase):
    def setUp(self):
        laboratorio = Laboratorio.objects.create(codigo='LAB', nome='Laboratório')
        local = Local.objects.create(laboratorio=laboratorio, nome='Bancada')
        self.equipamento = Equipamento.objects.create(nome='PC', codigo_patrimonio='PC-01', local=local)
        self.usuario = get_user_model().objects.create_user('cadastro', is_staff=True)
        self.usuario.user_permissions.add(Permission.objects.get(codename='view_equipamento'))
        self.url = reverse('paginas:etiqueta', args=[self.equipamento.pk])

    def test_imagem_real_e_url_publica(self):
        url = url_do_relato(self.equipamento)
        self.assertEqual(url, f'https://qreparo.example/e/{self.equipamento.qr_token}/')
        imagem = Image.open(BytesIO(base64.b64decode(gerar_qr(url).split(',')[1])))
        self.assertEqual(imagem.format, 'PNG')
        self.assertEqual(imagem.width, imagem.height)
        self.client.force_login(self.usuario)
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'data:image/png;base64,')
        self.assertContains(resposta, 'PC-01')
        self.assertContains(resposta, 'Bancada')
        self.assertIn('no-store', resposta['Cache-Control'])

    def test_acesso_exige_permissao_e_inativo_nao_gera_imagem(self):
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.usuario)
        self.equipamento.ativo = False
        self.equipamento.save()
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Este equipamento está desativado')
        self.assertNotContains(resposta, 'data:image/png;base64,')
        self.assertNotContains(resposta, 'Imprimir etiqueta')
        self.usuario.user_permissions.clear()
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_origem_precisa_ser_configurada_sem_caminho_ou_credenciais(self):
        for origem in ('', 'file:///tmp', 'https://user:password@example.com', 'https://example.com/caminho', 'https://example.com?x=1'):
            with self.subTest(origem=origem), override_settings(QREPARO_PUBLIC_URL=origem):
                with self.assertRaises(ImproperlyConfigured):
                    url_do_relato(self.equipamento)
