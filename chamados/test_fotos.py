from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from PIL import Image, ImageOps

from equipamentos.models import Equipamento, Laboratorio, Local
from .fotos import LIMITE_ENVIO, preparar_fotos
from .middleware import LimiteEnvioMiddleware
from .models import Chamado, Foto, Tag
from .servicos import criar_relato, resolver_selecionados


def imagem(formato='PNG', nome='foto.png', **opcoes):
    dados = BytesIO()
    Image.new('RGB', (32, 24), 'red').save(dados, format=formato, **opcoes)
    return SimpleUploadedFile(nome, dados.getvalue(), content_type='application/octet-stream')


class FotoTests(TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.configuracao = override_settings(QREPARO_FOTOS_ROOT=self.pasta.name)
        self.configuracao.enable()
        self.addCleanup(self.configuracao.disable)
        laboratorio = Laboratorio.objects.create(codigo='LAB', nome='Laboratório')
        local = Local.objects.create(laboratorio=laboratorio, nome='Bancada')
        self.equipamento = Equipamento.objects.create(nome='PC', codigo_patrimonio='PC-01', local=local)
        self.problema = Tag.objects.create(nome='Não liga')
        self.url = reverse('paginas:relato', args=[self.equipamento.qr_token])
        self.api = reverse('chamados:api_lista_ou_criar')
        self.tecnico = get_user_model().objects.create_user('tecnico')
        self.tecnico.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='chamados', codename__in=['view_chamado', 'change_chamado']))

    def criar(self, fotos=None):
        return criar_relato(token=self.equipamento.qr_token, problema=self.problema,
                            descricao='Falha', fotos=fotos if fotos is not None else [imagem()])

    def arquivos(self):
        return [p for p in Path(self.pasta.name).rglob('*') if p.is_file()]

    def test_png_jpeg_heic_convertidos_sem_metadados_e_sem_nome_original(self):
        for formato in ('PNG', 'JPEG', 'HEIF'):
            with self.subTest(formato=formato):
                exif = Image.Exif()
                exif[274] = 6
                exif[315] = 'Pessoa privada'
                enviada = imagem(formato, nome='nome-pessoal.heic', exif=exif)
                with Image.open(BytesIO(enviada.read())) as original:
                    tamanho_esperado = ImageOps.exif_transpose(original).size
                relato = self.criar([enviada])
                foto = relato.fotos.get()
                self.assertNotIn('nome-pessoal', foto.arquivo.name)
                self.assertEqual((foto.largura, foto.altura), tamanho_esperado)
                self.assertEqual(foto.tamanho, foto.arquivo.size)
                with foto.arquivo.open('rb') as arquivo, Image.open(arquivo) as resultado:
                    self.assertEqual(resultado.format, 'WEBP')
                    self.assertFalse(resultado.getexif())
                    self.assertNotIn('icc_profile', resultado.info)
                    self.assertNotIn('xmp', resultado.info)
                    self.assertEqual(getattr(resultado, 'n_frames', 1), 1)
                with self.assertRaises(ValueError):
                    _ = foto.arquivo.url

    def test_png_animado_usa_primeiro_quadro(self):
        dados = BytesIO()
        Image.new('RGB', (8, 8), 'red').save(
            dados, format='PNG', save_all=True, append_images=[Image.new('RGB', (8, 8), 'blue')])
        relato = self.criar([SimpleUploadedFile('animacao.png', dados.getvalue())])
        with relato.fotos.get().arquivo.open() as arquivo, Image.open(arquivo) as resultado:
            self.assertEqual(getattr(resultado, 'n_frames', 1), 1)
            self.assertGreater(resultado.getpixel((0, 0))[0], 200)

    def test_envio_html_e_api_com_duas_fotos_sem_revelar_urls_ao_aluno(self):
        for url in (self.url, self.api):
            with self.subTest(url=url):
                resposta = self.client.post(url, {'problema': self.problema.pk,
                    'qr_token': str(self.equipamento.qr_token), 'fotos': [imagem(), imagem('JPEG')]})
                self.assertEqual(resposta.status_code, 302 if url == self.url else 201)
                self.assertNotIn(b'/fotos/', resposta.content)
        self.assertEqual(Chamado.objects.count(), 2)
        self.assertEqual(Foto.objects.count(), 4)

    def test_envio_sem_foto_continua_funcionando(self):
        self.assertEqual(self.criar([]).fotos.count(), 0)

    def test_rejeita_tres_fotos_arquivo_falso_formato_invalido_e_truncado(self):
        invalido = SimpleUploadedFile('foto.png', b'<script>conteudo</script>', 'image/png')
        truncado = imagem()
        truncado = SimpleUploadedFile('foto.png', truncado.read()[:45], 'image/png')
        for fotos in ([imagem(), imagem(), imagem()], [imagem(), invalido],
                      [imagem('GIF')], [truncado]):
            with self.subTest(quantidade=len(fotos)):
                with self.assertRaises(ValidationError):
                    self.criar(fotos)
                self.assertFalse(Chamado.objects.exists())
                self.assertEqual(self.arquivos(), [])

    def test_limite_decimal_por_foto(self):
        arquivo = imagem()
        dados = arquivo.read()
        limite = SimpleUploadedFile('foto.png', dados + b'\0' * (10_000_000 - len(dados)))
        self.assertEqual(len(preparar_fotos([limite])), 1)
        excedido = SimpleUploadedFile('foto.png', dados + b'\0' * (10_000_001 - len(dados)))
        with self.assertRaisesMessage(ValidationError, '10 MB'):
            preparar_fotos([excedido])

    def test_limite_total_inclui_campos_e_estrutura_antes_do_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        resposta = cliente.post(self.api, b'x' * (LIMITE_ENVIO + 1), content_type='application/octet-stream')
        self.assertEqual(resposta.status_code, 413)
        self.assertFalse(Chamado.objects.exists())
        self.assertEqual(self.arquivos(), [])

    def test_limite_real_do_corpo_sem_confiar_apenas_no_cabecalho(self):
        middleware = LimiteEnvioMiddleware(lambda request: HttpResponse())
        for tamanho, status in ((LIMITE_ENVIO, 200), (LIMITE_ENVIO + 1, 413)):
            request = RequestFactory().post(self.api, b'', content_type='application/octet-stream')
            request.META['CONTENT_LENGTH'] = '1'
            request._stream = BytesIO(b'x' * tamanho)
            self.assertEqual(middleware(request).status_code, status)

    def test_api_rejeita_fotos_json_ou_campo_de_arquivo_desconhecido(self):
        resposta = self.client.post(self.api, {'qr_token': str(self.equipamento.qr_token),
            'problema': self.problema.pk, 'fotos': ['base64']}, content_type='application/json')
        self.assertEqual(resposta.status_code, 400)
        resposta = self.client.post(self.api, {'qr_token': str(self.equipamento.qr_token),
            'problema': self.problema.pk, 'anexo': imagem()})
        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(Chamado.objects.exists())

    def test_html_mostra_erro_sem_gravar_envio_incompleto(self):
        resposta = self.client.post(self.url, {'problema': self.problema.pk,
            'fotos': [imagem(), SimpleUploadedFile('falsa.jpg', b'errado')]})
        self.assertContains(resposta, 'Foto inválida')
        self.assertFalse(Chamado.objects.exists())

    def test_csrf_e_equipamento_inativo_impedem_upload(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(self.url, {'problema': self.problema.pk, 'fotos': imagem()}).status_code, 403)
        self.equipamento.ativo = False
        self.equipamento.save()
        with self.assertRaises(ValidationError):
            self.criar()
        self.assertFalse(Foto.objects.exists())
        self.assertEqual(self.arquivos(), [])

    def test_tecnico_consulta_lista_e_imagem_privada(self):
        relato = self.criar()
        foto = relato.fotos.get()
        self.client.force_login(self.tecnico)
        dados = self.client.get(reverse('chamados:api_detalhes', args=[relato.pk])).json()
        self.assertEqual(dados['fotos'][0]['url'], foto.get_absolute_url())
        self.assertNotIn('arquivo', dados['fotos'][0])
        resposta = self.client.get(foto.get_absolute_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Content-Type'], 'image/webp')
        self.assertIn('no-store', resposta['Cache-Control'])
        self.assertEqual(resposta['X-Content-Type-Options'], 'nosniff')
        self.assertTrue(b''.join(resposta.streaming_content).startswith(b'RIFF'))
        self.assertEqual(self.client.get(reverse('chamados:foto', args=[relato.pk + 1, foto.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('chamados:foto', args=[relato.pk, uuid4()])).status_code, 404)

    def test_anonimo_gestor_e_staff_sem_permissao_nao_veem_fotos(self):
        relato = self.criar()
        url = relato.fotos.get().get_absolute_url()
        for usuario in (None, get_user_model().objects.create_user('gestor'),
                        get_user_model().objects.create_user('cadastros', is_staff=True)):
            self.client.logout()
            if usuario:
                self.client.force_login(usuario)
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.get(reverse('chamados:api_detalhes', args=[relato.pk])).status_code, 403)

    def test_arquivo_ausente_retorna_404(self):
        foto = self.criar().fotos.get()
        foto.arquivo.storage.delete(foto.arquivo.name)
        self.client.force_login(self.tecnico)
        self.assertEqual(self.client.get(foto.get_absolute_url()).status_code, 404)

    def test_falha_na_segunda_gravacao_remove_primeiro_arquivo_e_relato(self):
        storage = Foto._meta.get_field('arquivo').storage
        salvar = storage.save
        chamadas = 0

        def falhar(nome, conteudo, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 2:
                raise OSError('indisponível')
            return salvar(nome, conteudo, **kwargs)

        with patch.object(storage, 'save', side_effect=falhar):
            with self.assertRaises(ValidationError):
                self.criar([imagem(), imagem()])
        self.assertFalse(Chamado.objects.exists())
        self.assertFalse(Foto.objects.exists())
        self.assertEqual(self.arquivos(), [])

    def test_falha_no_banco_remove_arquivo(self):
        with patch.object(Foto, 'save', side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.criar()
        self.assertFalse(Chamado.objects.exists())
        self.assertEqual(self.arquivos(), [])

    def test_posicoes_limitam_duas_fotos_no_banco(self):
        foto = self.criar().fotos.get()
        for posicao in (1, 3):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Foto.objects.create(chamado=foto.chamado, arquivo='nao-gravado.webp',
                    posicao=posicao, largura=1, altura=1, tamanho=1)

    def test_resolucao_descarta_fotos_e_conserva_contagem(self):
        relato = self.criar()
        url = relato.fotos.get().get_absolute_url()
        with self.captureOnCommitCallbacks(execute=True):
            resolver_selecionados(usuario=self.tecnico, equipamento_id=self.equipamento.pk, ids=[relato.pk])
        relato.refresh_from_db()
        self.assertTrue(relato.conteudo_removido)
        self.assertEqual(Chamado.objects.count(), 1)
        self.assertFalse(Foto.objects.exists())
        self.assertEqual(self.arquivos(), [])
        self.client.force_login(self.tecnico)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_rollback_da_resolucao_preserva_arquivo(self):
        relato = self.criar()
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    resolver_selecionados(usuario=self.tecnico, equipamento_id=self.equipamento.pk, ids=[relato.pk])
                    raise ValueError('abortar')
            except ValueError:
                pass
        self.assertEqual(Foto.objects.count(), 1)
        self.assertEqual(len(self.arquivos()), 1)

    def test_exclusao_do_relato_remove_arquivo_apos_commit(self):
        relato = self.criar()
        with self.captureOnCommitCallbacks(execute=True):
            relato.delete()
            self.assertEqual(len(self.arquivos()), 1)
        self.assertEqual(self.arquivos(), [])
