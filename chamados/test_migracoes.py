from uuid import uuid4

from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MigracaoLegadoTests(TransactionTestCase):
    def test_conversao_e_bloqueios_em_banco_separado(self):
        self.assertEqual(connection.vendor, 'postgresql')
        nome = f'test_qreparo_migracao_{uuid4().hex}'
        alias = 'migracao_legado'
        banco = connection.copy(alias=alias)
        banco.settings_dict['NAME'] = nome
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE {connection.ops.quote_name(nome)}')
        connections[alias] = banco
        try:
            antigos = [('equipamentos', '0001_initial'), ('chamados', '0001_initial'), ('admin', '0003_logentry_add_action_flag_choices')]
            novos = [('equipamentos', '0003_equipamento_categoria'), ('chamados', '0002_mvp_facil')]
            executor = MigrationExecutor(banco)
            executor.migrate(antigos)
            apps = executor.loader.project_state(antigos).apps
            Usuario = apps.get_model('auth', 'User')
            Equipamento = apps.get_model('equipamentos', 'Equipamento')
            Chamado = apps.get_model('chamados', 'Chamado')
            ContentType = apps.get_model('contenttypes', 'ContentType')
            LogEntry = apps.get_model('admin', 'LogEntry')
            usuario = Usuario.objects.using(alias).create(username='legado')
            equipamento = Equipamento.objects.using(alias).create(nome='PC', codigo_patrimonio='LEG-01', localizacao='Sala antiga')
            Equipamento.objects.using(alias).create(nome='Outro PC', codigo_patrimonio='LEG-02', localizacao='Outra sala')
            aberto = Chamado.objects.using(alias).create(
                equipamento=equipamento, solicitante=usuario, titulo='Título antigo',
                descricao='Texto aberto', status='CANCELADO',
            )
            resolvido = Chamado.objects.using(alias).create(
                equipamento=equipamento, solicitante=usuario, titulo='Título privado',
                descricao='Texto removido', status='RESOLVIDO', laudo_tecnico='Laudo privado',
            )
            tipo = ContentType.objects.using(alias).create(app_label='chamados', model='chamado')
            LogEntry.objects.using(alias).create(
                user=usuario, content_type=tipo, object_id=str(resolvido.pk),
                object_repr='Texto removido', action_flag=2, change_message='Laudo privado',
            )
            with self.assertRaisesRegex(RuntimeError, 'cancelados'):
                MigrationExecutor(banco).migrate(novos)
            Chamado.objects.using(alias).filter(pk=aberto.pk).update(status='ABERTO', descricao='x' * 251)
            with self.assertRaisesRegex(RuntimeError, '250'):
                MigrationExecutor(banco).migrate(novos)
            Chamado.objects.using(alias).filter(pk=aberto.pk).update(status='EM_ATENDIMENTO', descricao='Texto aberto')
            executor = MigrationExecutor(banco)
            executor.migrate(novos)
            apps = executor.loader.project_state(novos).apps
            Atual = apps.get_model('chamados', 'Chamado')
            aberto_atual = Atual.objects.using(alias).get(pk=aberto.pk)
            resolvido_atual = Atual.objects.using(alias).get(pk=resolvido.pk)
            self.assertEqual(aberto_atual.status, 'ABERTO')
            self.assertEqual(aberto_atual.descricao, 'Texto aberto')
            self.assertEqual(resolvido_atual.descricao, '')
            self.assertTrue(resolvido_atual.conteudo_removido)
            self.assertIsNotNone(resolvido_atual.data_conclusao)
            self.assertFalse(LogEntry.objects.using(alias).exists())
            EquipamentoAtual = apps.get_model('equipamentos', 'Equipamento')
            self.assertEqual(EquipamentoAtual.objects.using(alias).values('qr_token').distinct().count(), 2)
            self.assertEqual(EquipamentoAtual.objects.using(alias).filter(categoria='').count(), 2)
            self.assertNotIn('solicitante', [campo.name for campo in Atual._meta.fields])
        finally:
            banco.close()
            del connections[alias]
            with connection.cursor() as cursor:
                cursor.execute(f'DROP DATABASE {connection.ops.quote_name(nome)}')
