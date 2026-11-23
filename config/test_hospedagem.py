import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from io import StringIO
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command, CommandError
from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings


@skipUnless(importlib.util.find_spec('dj_database_url'), 'Instale requirements-railway.txt.')
class ConfiguracaoHospedagemTests(SimpleTestCase):
    def executar(self, **variaveis):
        ambiente = dict(os.environ, DJANGO_SETTINGS_MODULE='config.settings_railway',
            DJANGO_DEBUG='false', DJANGO_SECRET_KEY='teste-0123456789-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLM',
            DJANGO_ALLOWED_HOSTS='feira.example', QREPARO_PUBLIC_URL='https://feira.example',
            DATABASE_URL='postgresql://usuario:senha%40teste@banco.example:5432/feira?sslmode=require',
            QREPARO_FOTOS_ROOT=str(Path(settings.BASE_DIR).parent / 'volume-teste' / 'fotos'))
        ambiente.update(variaveis)
        return subprocess.run([sys.executable, '-c',
            'import django; django.setup(); '
            'from django.core.checks import run_checks; '
            'from django.conf import settings as s; import json; '
            'assert not [c for c in run_checks(include_deployment_checks=True) if not c.is_silenced()]; '
            'print(json.dumps([s.DATABASES["default"], s.CSRF_TRUSTED_ORIGINS, '
            's.SESSION_COOKIE_SECURE, s.ALLOWED_HOSTS]))'],
            env=ambiente, capture_output=True, text=True)

    def test_url_postgres_e_origem_https(self):
        resultado = self.executar()
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        banco, origens, cookie, hosts = json.loads(resultado.stdout)
        self.assertEqual(banco['PASSWORD'], 'senha@teste')
        self.assertEqual(banco['NAME'], 'feira')
        self.assertEqual(banco['OPTIONS']['sslmode'], 'require')
        self.assertTrue(banco['CONN_HEALTH_CHECKS'])
        self.assertEqual(origens, ['https://feira.example'])
        self.assertTrue(cookie)
        self.assertIn('healthcheck.railway.app', hosts)

    def test_recusa_configuracoes_inseguras_sem_usar_banco_local(self):
        for variaveis in [dict(DJANGO_DEBUG='true'), dict(DJANGO_SECRET_KEY='curta'),
                dict(DJANGO_ALLOWED_HOSTS='*'), dict(DATABASE_URL=''),
                dict(DATABASE_URL='sqlite:///db.sqlite3'), dict(QREPARO_PUBLIC_URL='http://feira.example'),
                dict(QREPARO_PUBLIC_URL='https://outro.example'), dict(QREPARO_FOTOS_ROOT='relativo'),
                dict(QREPARO_FOTOS_ROOT=str(settings.STATIC_ROOT / 'fotos'))]:
            with self.subTest(variaveis=variaveis):
                self.assertNotEqual(self.executar(**variaveis).returncode, 0)


class SaudeTests(TestCase):
    def test_banco_disponivel(self):
        resposta = self.client.get('/saude/')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {'status': 'ok'})
        self.assertIn('no-store', resposta['Cache-Control'])

    def test_indisponibilidade_nao_expoe_detalhes(self):
        with patch('config.saude.connection.cursor', side_effect=DatabaseError('segredo')):
            resposta = self.client.get('/saude/')
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta.json(), {'status': 'indisponivel'})

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r'^saude/$'],
        SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_healthcheck_sem_redirect_e_https_atras_do_proxy(self):
        self.assertEqual(self.client.get('/saude/').status_code, 200)
        self.assertEqual(self.client.get('/entrar/').status_code, 301)
        self.assertEqual(self.client.get('/entrar/', HTTP_X_FORWARDED_PROTO='https').status_code, 200)


class VolumeTests(TestCase):
    def test_volume_ausente_ou_pasta_externa_impede_inicializacao(self):
        with patch.dict(os.environ, {'RAILWAY_VOLUME_MOUNT_PATH': ''}):
            with self.assertRaisesMessage(CommandError, 'Volume ausente'):
                call_command('verificar_hospedagem', stdout=StringIO())
        with TemporaryDirectory() as pasta, patch.dict(os.environ, {'RAILWAY_VOLUME_MOUNT_PATH': pasta}):
            with override_settings(QREPARO_FOTOS_ROOT=Path(pasta).parent / 'fora'):
                with self.assertRaisesMessage(CommandError, 'subpasta'):
                    call_command('verificar_hospedagem', stdout=StringIO())

    def test_verifica_volume_e_detecta_foto_perdida_ou_alterada(self):
        from chamados.test_fotos import imagem
        from chamados.models import Tag
        from chamados.servicos import criar_relato
        from equipamentos.models import Equipamento, Laboratorio, Local

        with TemporaryDirectory() as pasta, patch.dict(os.environ, {'RAILWAY_VOLUME_MOUNT_PATH': pasta}):
            with override_settings(QREPARO_FOTOS_ROOT=Path(pasta) / 'fotos'):
                lab = Laboratorio.objects.create(codigo='LAB', nome='Laboratório')
                local = Local.objects.create(laboratorio=lab, nome='Bancada')
                equipamento = Equipamento.objects.create(nome='PC', codigo_patrimonio='PC', local=local)
                relato = criar_relato(token=equipamento.qr_token,
                    problema=Tag.objects.create(nome='Não liga'), descricao='', fotos=[imagem()])
                foto = relato.fotos.get()
                arquivo = Path(foto.arquivo.path)
                original = arquivo.read_bytes()
                call_command('verificar_hospedagem', fotos=True, stdout=StringIO())
                arquivo.write_bytes(b'incompleto')
                with self.assertRaisesMessage(CommandError, '1 foto(s)'):
                    call_command('verificar_hospedagem', fotos=True, stdout=StringIO())
                arquivo.unlink()
                with self.assertRaisesMessage(CommandError, '1 foto(s)'):
                    call_command('verificar_hospedagem', fotos=True, stdout=StringIO())
                arquivo.write_bytes(original)
                call_command('verificar_hospedagem', fotos=True, stdout=StringIO())


@skipUnless(importlib.util.find_spec('whitenoise'), 'Instale requirements-railway.txt.')
class EstaticosHospedagemTests(SimpleTestCase):
    def test_collectstatic_e_acesso_sem_publicar_volume(self):
        from django.templatetags.static import static
        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            fotos = raiz / 'fotos'
            fotos.mkdir()
            (fotos / 'privada.webp').write_bytes(b'privado')
            with override_settings(DEBUG=False, STATIC_ROOT=raiz / 'static', QREPARO_FOTOS_ROOT=fotos,
                    STORAGES={'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}},
                    MIDDLEWARE=[settings.MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware',
                        *settings.MIDDLEWARE[1:]], WHITENOISE_AUTOREFRESH=False, WHITENOISE_USE_FINDERS=False):
                call_command('collectstatic', interactive=False, verbosity=0)
                resposta = self.client.get(static('css/app.css'))
                self.assertEqual(resposta.status_code, 200)
                resposta.close()
                for url in ['/static/privada.webp', '/midia_privada/privada.webp', '/dados/fotos/privada.webp']:
                    self.assertEqual(self.client.get(url).status_code, 404)
