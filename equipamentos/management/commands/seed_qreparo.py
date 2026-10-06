from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from equipamentos.models import Equipamento
from chamados.models import Chamado

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados acadêmicos de teste para o QReparo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando carga de dados do QReparo...'))

        # 1. Usuários de teste
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@universidade.edu.br',
                'first_name': 'Administrador',
                'last_name': 'Geral',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if _:
            admin_user.set_password('admin123')
            admin_user.save()

        tecnico_user, _ = User.objects.get_or_create(
            username='carlos_tecnico',
            defaults={
                'email': 'carlos.ti@universidade.edu.br',
                'first_name': 'Carlos',
                'last_name': 'Menezes',
                'is_staff': True,
            }
        )
        if _:
            tecnico_user.set_password('senha123')
            tecnico_user.save()

        prof_user, _ = User.objects.get_or_create(
            username='prof_ana',
            defaults={
                'email': 'ana.silva@universidade.edu.br',
                'first_name': 'Profa. Ana',
                'last_name': 'Silva',
            }
        )
        if _:
            prof_user.set_password('senha123')
            prof_user.save()

        # 2. Equipamentos Universitários
        equipamentos_dados = [
            {
                'nome': 'Projetor Epson PowerLite 109W',
                'codigo_patrimonio': 'PAT-2024-001',
                'categoria': Equipamento.CATEGORIA_AUDIOVISUAL,
                'localizacao': 'Bloco B - Sala de Aula 201',
                'status': Equipamento.STATUS_OPERACIONAL,
                'descricao': 'Projetor HDMI/VGA montado no teto. Lâmpada trocada em 02/2026.'
            },
            {
                'nome': 'Estação de Trabalho Dell OptiPlex 7090 (PC 08)',
                'codigo_patrimonio': 'PAT-2024-042',
                'categoria': Equipamento.CATEGORIA_INFORMATICA,
                'localizacao': 'Bloco C - Laboratório de Informática 3',
                'status': Equipamento.STATUS_MANUTENCAO,
                'descricao': 'Intel Core i7, 32GB RAM, SSD 512GB. Apresentando desligamento repentino.'
            },
            {
                'nome': 'Osciloscópio Digital Tektronix TBS1052B',
                'codigo_patrimonio': 'PAT-2023-115',
                'categoria': Equipamento.CATEGORIA_LABORATORIO,
                'localizacao': 'Bloco E - Laboratório de Eletrônica Aplicada',
                'status': Equipamento.STATUS_OPERACIONAL,
                'descricao': 'Bancada 04 - 50 MHz, 2 canais, taxa de amostragem de 1 GS/s.'
            },
            {
                'nome': 'Ar Condicionado Split Inverter Elgin 30.000 BTUs',
                'codigo_patrimonio': 'PAT-2022-089',
                'categoria': Equipamento.CATEGORIA_CLIMATIZACAO,
                'localizacao': 'Bloco D - Data Center Central',
                'status': Equipamento.STATUS_OPERACIONAL,
                'descricao': 'Unidade redundante de resfriamento do rack principal de servidores.'
            },
            {
                'nome': 'Microscópio Óptico Binocular Olympus CX23',
                'codigo_patrimonio': 'PAT-2023-067',
                'categoria': Equipamento.CATEGORIA_LABORATORIO,
                'localizacao': 'Bloco F - Laboratório de Biologia Celular',
                'status': Equipamento.STATUS_INOPERANTE,
                'descricao': 'Foco macrométrico travado e lâmpada LED queimada.'
            },
            {
                'nome': 'Switch Gerenciável Cisco Catalyst 2960-X 48 Portas',
                'codigo_patrimonio': 'PAT-2021-014',
                'categoria': Equipamento.CATEGORIA_REDE,
                'localizacao': 'Bloco A - Rack de Telecomunicações Térreo',
                'status': Equipamento.STATUS_OPERACIONAL,
                'descricao': 'Switch core do anel de fibra óptica da biblioteca.'
            },
        ]

        equipamentos_criados = {}
        for eq_d in equipamentos_dados:
            obj, _ = Equipamento.objects.update_or_create(
                codigo_patrimonio=eq_d['codigo_patrimonio'],
                defaults=eq_d
            )
            equipamentos_criados[obj.codigo_patrimonio] = obj

        # 3. Chamados de Teste
        chamados_dados = [
            {
                'titulo': 'PC 08 desligando sozinho durante aulas práticas',
                'descricao': 'Durante o uso do software de compilação, o microcomputador desliga repentinamente. Suspeita de superaquecimento da CPU.',
                'equipamento': equipamentos_criados['PAT-2024-042'],
                'solicitante': prof_user,
                'tecnico_responsavel': tecnico_user,
                'prioridade': Chamado.PRIORIDADE_ALTA,
                'status': Chamado.STATUS_EM_ATENDIMENTO,
                'laudo_tecnico': 'Em análise na bancada: pasta térmica ressecada e cooler com acúmulo de poeira. Substituição agendada.'
            },
            {
                'titulo': 'Mecanismo de foco macrométrico travado',
                'descricao': 'O botão lateral do microscópio não gira. Alunos não conseguem focar lâminas para a aula de histologia.',
                'equipamento': equipamentos_criados['PAT-2023-067'],
                'solicitante': prof_user,
                'tecnico_responsavel': None,
                'prioridade': Chamado.PRIORIDADE_URGENTE,
                'status': Chamado.STATUS_ABERTO,
                'laudo_tecnico': ''
            },
            {
                'titulo': 'Limpeza periódica de filtro de ar',
                'descricao': 'Manutenção preventiva trimestral concluída com sucesso.',
                'equipamento': equipamentos_criados['PAT-2022-089'],
                'solicitante': admin_user,
                'tecnico_responsavel': tecnico_user,
                'prioridade': Chamado.PRIORIDADE_BAIXA,
                'status': Chamado.STATUS_RESOLVIDO,
                'laudo_tecnico': 'Filtros lavados, pressão de gás refrigerante aferida (130 PSI) e teste de dreno executado. Equipamento 100% operacional.'
            }
        ]

        for ch_d in chamados_dados:
            Chamado.objects.get_or_create(
                titulo=ch_d['titulo'],
                equipamento=ch_d['equipamento'],
                defaults=ch_d
            )

        self.stdout.write(self.style.SUCCESS('Carga de dados de teste concluída com sucesso!'))
        self.stdout.write(self.style.SUCCESS(f'Superusuário: admin / admin123'))
        self.stdout.write(self.style.SUCCESS(f'Técnico: carlos_tecnico / senha123'))
