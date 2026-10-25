from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, connection
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from equipamentos.models import Equipamento, Laboratorio, Local
from .consultas import contagem_tecnica
from .models import Chamado, Tag
from .servicos import ConflitoSelecao, resolver_selecionados


def preparar():
    laboratorio = Laboratorio.objects.create(codigo='L1', nome='Laboratório original')
    local = Local.objects.create(laboratorio=laboratorio, nome='Bancada')
    equipamento = Equipamento.objects.create(nome='PC', codigo_patrimonio='PC-01', local=local)
    problema = Tag.objects.create(nome='Não liga')
    usuario = get_user_model().objects.create_user('tecnico')
    usuario.user_permissions.add(*Permission.objects.filter(
        content_type__app_label='chamados', codename__in=['view_chamado', 'change_chamado'],
    ))
    relatos = [Chamado.objects.create(equipamento=equipamento, problema=problema, descricao=f'texto {i}') for i in range(3)]
    return equipamento, usuario, relatos


class AtendimentoTests(TestCase):
    def setUp(self):
        self.equipamento, self.usuario, self.relatos = preparar()
        self.client.force_login(self.usuario)
        self.conferencia = reverse('paginas:conferencia', args=[self.equipamento.pk])
        self.resolver = reverse('paginas:resolver', args=[self.equipamento.pk])

    def token(self, ids):
        resposta = self.client.post(self.conferencia, {'selecionados': ids})
        self.assertEqual(resposta.status_code, 200)
        return resposta.context['selection_token']

    def test_fluxo_parcial_e_ultimo_relato(self):
        token = self.token([r.pk for r in self.relatos[:2]])
        self.assertEqual(Chamado.objects.filter(status=Chamado.ABERTO).count(), 3)
        resposta = self.client.post(self.resolver, {'selection_token': token})
        self.assertRedirects(resposta, reverse('paginas:relatos_equipamento', args=[self.equipamento.pk]))
        for relato in self.relatos[:2]:
            relato.refresh_from_db()
            self.assertEqual(relato.descricao, '')
            self.assertTrue(relato.conteudo_removido)
            self.assertIsNotNone(relato.data_conclusao)
        ultimo = self.relatos[2]
        ultimo.refresh_from_db()
        self.assertEqual(ultimo.descricao, 'texto 2')
        self.assertEqual(self.client.post(self.resolver, {'selection_token': token}).status_code, 409)
        token = self.token([ultimo.pk])
        self.assertRedirects(self.client.post(self.resolver, {'selection_token': token}), reverse('paginas:painel'))
        self.assertContains(self.client.get('/tecnico/'), 'Nenhum equipamento com relatos abertos')
        self.assertTrue(Equipamento.objects.filter(pk=self.equipamento.pk).exists())

    def test_assinatura_nao_aceita_alteracao_ou_outra_sessao(self):
        token = self.token([self.relatos[0].pk])
        self.assertEqual(self.client.post(self.resolver, {'selection_token': token + 'x'}).status_code, 400)
        outro = Client()
        outro.force_login(self.usuario)
        self.assertEqual(outro.post(self.resolver, {'selection_token': token}).status_code, 400)
        self.assertEqual(Chamado.objects.filter(status=Chamado.ABERTO).count(), 3)

    def test_conflito_nao_resolve_outros_itens_do_lote(self):
        token = self.token([r.pk for r in self.relatos[:2]])
        resolver_selecionados(usuario=self.usuario, equipamento_id=self.equipamento.pk, ids=[self.relatos[0].pk])
        self.assertEqual(self.client.post(self.resolver, {'selection_token': token}).status_code, 409)
        self.relatos[1].refresh_from_db()
        self.assertEqual(self.relatos[1].status, Chamado.ABERTO)
        self.assertEqual(self.relatos[1].descricao, 'texto 1')

    def test_selecao_vazia_duplicada_inexistente_e_outro_equipamento(self):
        for ids in ([], ['abc'], [self.relatos[0].pk, self.relatos[0].pk]):
            self.assertEqual(self.client.post(self.conferencia, {'selecionados': ids}).status_code, 400)
        self.assertEqual(self.client.post(self.conferencia, {'selecionados': [999999]}).status_code, 409)
        outro = Equipamento.objects.create(nome='Outro', codigo_patrimonio='PC-02', local=self.equipamento.local)
        relato = Chamado.objects.create(equipamento=outro, problema=self.relatos[0].problema)
        with self.assertRaises(ConflitoSelecao):
            resolver_selecionados(usuario=self.usuario, equipamento_id=self.equipamento.pk, ids=[self.relatos[0].pk, relato.pk])
        self.assertFalse(Chamado.objects.filter(status=Chamado.RESOLVIDO).exists())

    def test_falha_na_segunda_gravacao_desfaz_descarte_da_primeira(self):
        salvar = Chamado.save

        def falhar(relato, *args, **kwargs):
            if relato.pk == self.relatos[1].pk:
                raise RuntimeError('falha de teste')
            return salvar(relato, *args, **kwargs)

        with patch.object(Chamado, 'save', falhar), self.assertRaises(RuntimeError):
            resolver_selecionados(usuario=self.usuario, equipamento_id=self.equipamento.pk, ids=[r.pk for r in self.relatos])
        self.assertEqual(Chamado.objects.filter(status=Chamado.ABERTO).count(), 3)
        self.assertFalse(Chamado.objects.filter(descricao='').exists())

    def test_revogacao_e_somente_leitura(self):
        token = self.token([self.relatos[0].pk])
        self.assertTrue(self.usuario.has_perm('chamados.change_chamado'))
        self.usuario.user_permissions.remove(Permission.objects.get(codename='change_chamado'))
        self.assertEqual(self.client.post(self.resolver, {'selection_token': token}).status_code, 403)
        with self.assertRaises(PermissionDenied):
            resolver_selecionados(usuario=self.usuario, equipamento_id=self.equipamento.pk, ids=[self.relatos[0].pk])
        detalhe = self.client.get(reverse('paginas:relatos_equipamento', args=[self.equipamento.pk]))
        self.assertNotContains(detalhe, 'name="selecionados"')

    def test_contagem_preserva_laboratorio_e_painel_mostra_inativos(self):
        antigo = self.equipamento.local.laboratorio_id
        laboratorio = Laboratorio.objects.create(codigo='L2', nome='Novo laboratório')
        self.equipamento.local = Local.objects.create(laboratorio=laboratorio, nome='Nova bancada')
        self.equipamento.ativo = False
        self.equipamento.save()
        self.assertContains(self.client.get('/tecnico/'), 'PC-01')
        resolver_selecionados(usuario=self.usuario, equipamento_id=self.equipamento.pk, ids=[self.relatos[0].pk])
        linha = contagem_tecnica().get()
        self.assertEqual(linha['laboratorio_id'], antigo)
        self.assertEqual((linha['abertos'], linha['resolvidos'], linha['total']), (2, 1, 3))
        resposta = self.client.get('/tecnico/contagem/')
        self.assertContains(resposta, 'Laboratório original')
        self.assertNotContains(resposta, 'texto 1')

    def test_csrf_e_metodos_nao_permitem_resolucao_por_get(self):
        self.assertEqual(self.client.get(self.resolver).status_code, 405)
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(self.conferencia, {'selecionados': [self.relatos[0].pk]}).status_code, 403)
        self.assertEqual(cliente.post(self.resolver, {}).status_code, 403)


class ConcorrenciaLoteTests(TransactionTestCase):
    def test_lotes_sobrepostos_resolvem_apenas_um_lote(self):
        self.assertEqual(connection.vendor, 'postgresql')
        equipamento, usuario, relatos = preparar()
        barreira = Barrier(2)

        def resolver(ids):
            close_old_connections()
            try:
                barreira.wait(timeout=10)
                try:
                    resolver_selecionados(usuario=usuario, equipamento_id=equipamento.pk, ids=ids)
                    return 'resolvido'
                except ConflitoSelecao:
                    return 'conflito'
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            tarefas = [pool.submit(resolver, [relatos[0].pk, relatos[1].pk]),
                       pool.submit(resolver, [relatos[1].pk, relatos[2].pk])]
            self.assertCountEqual([t.result(timeout=20) for t in tarefas], ['resolvido', 'conflito'])
        self.assertEqual(Chamado.objects.filter(status=Chamado.RESOLVIDO, descricao='').count(), 2)
        self.assertEqual(Chamado.objects.filter(status=Chamado.ABERTO).count(), 1)
