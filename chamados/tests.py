from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Barrier

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, close_old_connections
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase, skipUnlessDBFeature

from equipamentos.models import Equipamento, Laboratorio, Local
from .models import Chamado, ConflitoEstado, Tag


def preparar():
    lab = Laboratorio.objects.create(codigo='L1', nome='Laboratório')
    local = Local.objects.create(laboratorio=lab, nome='Bancada')
    eq = Equipamento.objects.create(nome='PC', codigo_patrimonio='P1', local=local)
    tag = Tag.objects.create(nome='Não liga')
    tecnico = get_user_model().objects.create_user(username='tecnico')
    tecnico.user_permissions.add(*Permission.objects.filter(
        content_type__app_label='chamados', codename__in=['view_chamado', 'change_chamado']))
    return eq, tag, tecnico


class AdaptacaoTests(TestCase):
    def setUp(self):
        self.eq, self.tag, self.tecnico = preparar()
        self.outro = Tag.objects.get(outro=True)

    def relato(self, descricao='Texto privado'):
        return Chamado.objects.create(equipamento=self.eq, problema=self.tag, descricao=descricao)

    def enviar(self, **extra):
        dados = {'qr_token': str(self.eq.qr_token), 'problema': self.tag.pk}
        dados.update(extra)
        return self.client.post('/chamados/api/', dados, content_type='application/json')

    def test_envio_sem_autoria_e_sem_titulo(self):
        self.assertEqual(self.enviar(laboratorio=999, equipamento_id=999).status_code, 201)
        chamado = Chamado.objects.get()
        self.assertEqual(chamado.laboratorio_id, self.eq.local.laboratorio_id)
        self.assertEqual(chamado.equipamento_id, self.eq.pk)
        self.assertEqual(chamado.descricao, '')
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertNotIn('solicitante', [f.name for f in Chamado._meta.fields])
        self.assertEqual(self.enviar().json(), {'mensagem': 'Relato recebido.'})

    def test_validacao_apenas_um_problema_e_descricao_condicional(self):
        for extra in [
            {'problema': self.outro.pk, 'descricao': '  '},
            {'problema': [self.tag.pk, self.outro.pk]},
            {'descricao': 'x' * 251}, {'descricao': {}}, {'problema': True},
            {'qr_token': 'invalido'},
        ]:
            self.assertEqual(self.enviar(**extra).status_code, 400)
        self.assertEqual(Chamado.objects.count(), 0)
        self.assertEqual(self.enviar(problema=self.outro.pk, descricao='x' * 250).status_code, 201)
        self.assertEqual(self.client.post('/chamados/api/', '[]', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/chamados/api/', '{', content_type='application/json').status_code, 400)
        self.assertEqual(self.enviar(problema=99999).status_code, 404)

    def test_equipamento_inativo(self):
        self.eq.ativo = False
        self.eq.save()
        self.assertEqual(self.enviar().status_code, 400)
        self.assertFalse(Chamado.objects.exists())

    def test_csrf_nao_e_ignorado(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post('/chamados/api/', {}).status_code, 403)
        cliente.force_login(self.tecnico)
        self.assertEqual(cliente.post('/chamados/api/1/status/', {'status': 'RESOLVIDO'}).status_code, 403)

    def test_leituras_exigem_permissao_tecnica(self):
        relato = self.relato()
        urls = ['/chamados/api/', f'/chamados/api/{relato.pk}/',
                '/equipamentos/api/', f'/equipamentos/api/{self.eq.pk}/']
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        staff = get_user_model().objects.create_user(username='cadastros', is_staff=True)
        self.client.force_login(staff)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.tecnico)
        for url in urls:
            resposta = self.client.get(url)
            self.assertEqual(resposta.status_code, 200)
            self.assertIn('no-store', resposta['Cache-Control'])
            self.assertEqual(resposta['Referrer-Policy'], 'no-referrer')

    def test_endpoint_antigo_nao_contorna_conferencia(self):
        relato = self.relato()
        self.client.force_login(self.tecnico)
        url = f'/chamados/api/{relato.pk}/status/'
        self.assertEqual(self.client.post(url, {'status': 'RESOLVIDO'}).status_code, 410)
        relato.refresh_from_db()
        self.assertEqual(relato.status, Chamado.ABERTO)
        self.assertEqual(relato.descricao, 'Texto privado')

    def test_somente_leitura_nao_pode_resolver(self):
        user = get_user_model().objects.create_user(username='leitura')
        user.user_permissions.add(Permission.objects.get(codename='view_chamado'))
        self.client.force_login(user)
        relato = self.relato()
        self.assertEqual(self.client.post(f'/chamados/api/{relato.pk}/status/', {'status': 'RESOLVIDO'}).status_code, 403)
        self.assertEqual(self.client.post('/equipamentos/api/', {'nome': 'Novo'}).status_code, 405)

    def test_snapshot_e_desativacao_preservam_historico(self):
        relato = self.relato()
        original = relato.laboratorio_id
        lab = Laboratorio.objects.create(codigo='L2', nome='Outro laboratório')
        local = Local.objects.create(laboratorio=lab, nome='Outra bancada')
        self.eq.local = local
        self.eq.save()
        relato.status = Chamado.RESOLVIDO
        relato.save()
        relato.refresh_from_db()
        self.assertEqual(relato.laboratorio_id, original)
        with self.assertRaises(ProtectedError):
            self.eq.delete()
        relato.status = Chamado.ABERTO
        with self.assertRaises(ConflitoEstado):
            relato.save()

    def test_modelo_valida_sem_depender_do_endpoint(self):
        with self.assertRaises(ValidationError):
            self.relato('x' * 251)
        with self.assertRaises(ValidationError):
            Chamado.objects.create(equipamento=self.eq, problema=self.outro)
        self.assertNotIn(Chamado, admin.site._registry)
        self.assertNotIn('Texto privado', str(self.relato()))

    def test_seed_sem_contas_senhas_ou_relatos_adicionais(self):
        for _ in range(2):
            call_command('seed_qreparo', stdout=StringIO())
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Equipamento.objects.filter(codigo_patrimonio='DEMO-001').count(), 1)
        self.assertFalse(Chamado.objects.exists())


class ConcorrenciaIndividualTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_dois_atendimentos_do_mesmo_relato_nao_reabrem_nem_sobrescrevem(self):
        eq, tag, _ = preparar()
        relato = Chamado.objects.create(equipamento=eq, problema=tag, descricao='Descartar')
        barreira = Barrier(2)

        def resolver():
            close_old_connections()
            try:
                copia = Chamado.objects.get(pk=relato.pk)
                barreira.wait(timeout=10)
                copia.status = Chamado.RESOLVIDO
                try:
                    copia.save(update_fields=['status'])
                    return 'resolvido'
                except ConflitoEstado:
                    return 'conflito'
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = [pool.submit(resolver) for _ in range(2)]
            self.assertCountEqual([r.result(timeout=20) for r in resultados], ['resolvido', 'conflito'])
        relato.refresh_from_db()
        self.assertEqual(relato.descricao, '')
        self.assertEqual(relato.status, Chamado.RESOLVIDO)
