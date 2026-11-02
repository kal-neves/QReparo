from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from chamados.models import Chamado, Tag
from .admin import EquipamentoForm
from .models import Equipamento, Laboratorio, Local


class CadastroTests(TestCase):
    def setUp(self):
        self.laboratorio = Laboratorio.objects.create(codigo='L1', nome='Laboratório 1')
        self.local = Local.objects.create(laboratorio=self.laboratorio, nome='Bancada 1')
        self.equipamento = Equipamento.objects.create(
            nome='Computador', codigo_patrimonio='PC-01', descricao='Computador da bancada', local=self.local,
        )
        self.admin = get_user_model().objects.create_superuser('admin', password='senha-de-teste')
        self.client.force_login(self.admin)

    def test_formulario_exige_descricao_e_identificacao_unica(self):
        dados = {'nome': 'Outro', 'codigo_patrimonio': 'PC-02', 'local': self.local.pk, 'ativo': True}
        form = EquipamentoForm(data=dados)
        self.assertFalse(form.is_valid())
        self.assertIn('descricao', form.errors)
        self.assertIn('categoria', form.errors)
        dados['descricao'] = 'Computador de apoio'
        dados['categoria'] = 'Computador'
        form = EquipamentoForm(data=dados)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.fields['codigo_patrimonio'].label, 'Identificação')
        dados['codigo_patrimonio'] = self.equipamento.codigo_patrimonio
        self.assertIn('codigo_patrimonio', EquipamentoForm(data=dados).errors)

    def test_edicao_do_local_nao_transfere_laboratorio(self):
        outro = Laboratorio.objects.create(codigo='L2', nome='Laboratório 2')
        url = reverse('admin:equipamentos_local_change', args=[self.local.pk])
        resposta = self.client.post(url, {'nome': 'Bancada nova', 'laboratorio': outro.pk})
        self.assertEqual(resposta.status_code, 302)
        self.local.refresh_from_db()
        self.assertEqual(self.local.nome, 'Bancada nova')
        self.assertEqual(self.local.laboratorio_id, self.laboratorio.pk)

    def test_historico_bloqueia_exclusao_individual_e_em_lote(self):
        Chamado.objects.create(equipamento=self.equipamento, problema=Tag.objects.get(outro=True), descricao='Falha')
        url = reverse('admin:equipamentos_equipamento_delete', args=[self.equipamento.pk])
        self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 200)
        url = reverse('admin:equipamentos_equipamento_changelist')
        self.client.post(url, {'action': 'delete_selected', '_selected_action': [self.equipamento.pk], 'post': 'yes'})
        self.assertTrue(Equipamento.objects.filter(pk=self.equipamento.pk).exists())
        token = self.equipamento.qr_token
        self.equipamento.ativo = False
        self.equipamento.save()
        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.qr_token, token)
        self.assertEqual(self.equipamento.chamados.count(), 1)

    def test_staff_sem_permissao_nao_altera_equipamento(self):
        usuario = get_user_model().objects.create_user('cadastro', is_staff=True)
        usuario.user_permissions.add(Permission.objects.get(codename='view_equipamento'))
        self.client.force_login(usuario)
        url = reverse('admin:equipamentos_equipamento_change', args=[self.equipamento.pk])
        self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_seed_cria_dois_equipamentos_sem_sobrescrever_edicoes(self):
        call_command('seed_qreparo', stdout=StringIO())
        primeiro = Equipamento.objects.get(codigo_patrimonio='DEMO-001')
        primeiro.nome = 'Nome escolhido pela equipe'
        primeiro.categoria = 'Estação de trabalho'
        primeiro.save()
        call_command('seed_qreparo', stdout=StringIO())
        primeiro.refresh_from_db()
        exemplos = Equipamento.objects.filter(codigo_patrimonio__startswith='DEMO-')
        self.assertEqual(exemplos.count(), 2)
        self.assertEqual(exemplos.values('local').distinct().count(), 2)
        self.assertFalse(exemplos.filter(descricao='').exists())
        self.assertEqual(primeiro.nome, 'Nome escolhido pela equipe')
        self.assertEqual(primeiro.categoria, 'Estação de trabalho')
        self.assertEqual(exemplos.get(codigo_patrimonio='DEMO-002').categoria, 'Computador')
        self.assertFalse(Chamado.objects.exists())
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_seed_prepara_catalogo_completo_sem_duplicar(self):
        for _ in range(2):
            call_command('seed_qreparo', stdout=StringIO())
        self.assertSetEqual(set(Tag.objects.values_list('nome', flat=True)), {
            'Não liga', 'Sem internet', 'Lentidão', 'Periférico', 'Software',
            'Monitor', 'Teclado/mouse', 'Áudio', 'Impressora', 'Outro problema',
        })
        self.assertEqual(Tag.objects.filter(outro=True).count(), 1)
        self.assertTrue(Tag.objects.get(nome='Outro problema').outro)

    def test_seed_preserva_classificacoes_existentes_e_relato(self):
        problema = Tag.objects.create(nome='Sem imagem')
        relato = Chamado.objects.create(equipamento=self.equipamento, problema=problema)
        outro = Tag.objects.get(outro=True)
        outro.nome = 'Outro problema revisado'
        outro.save()
        for _ in range(2):
            call_command('seed_qreparo', stdout=StringIO())
        relato.refresh_from_db()
        outro.refresh_from_db()
        self.assertEqual(relato.problema_id, problema.pk)
        self.assertEqual(relato.problema.nome, 'Sem imagem')
        self.assertEqual(outro.nome, 'Outro problema revisado')
        self.assertEqual(Tag.objects.filter(outro=True).count(), 1)
        self.assertEqual(Tag.objects.count(), 11)

    def test_admin_salva_categoria_e_filtra_equipamentos(self):
        url = reverse('admin:equipamentos_equipamento_change', args=[self.equipamento.pk])
        resposta = self.client.post(url, {
            'nome': self.equipamento.nome, 'codigo_patrimonio': self.equipamento.codigo_patrimonio,
            'descricao': self.equipamento.descricao, 'categoria': 'Computador',
            'local': self.local.pk, 'ativo': True,
        })
        self.assertEqual(resposta.status_code, 302)
        self.equipamento.refresh_from_db()
        self.assertEqual(self.equipamento.categoria, 'Computador')
        Equipamento.objects.create(
            nome='Impressora', codigo_patrimonio='IMP-01', categoria='Impressora', local=self.local,
        )
        url = reverse('admin:equipamentos_equipamento_changelist')
        for filtro in ({'categoria': 'Computador'}, {'q': 'Computador'}):
            with self.subTest(filtro=filtro):
                resposta = self.client.get(url, filtro)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(list(resposta.context['cl'].queryset), [self.equipamento])
