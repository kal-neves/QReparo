from django.core.management.base import BaseCommand
from django.db import transaction
from chamados.models import Tag
from equipamentos.models import Equipamento, Laboratorio, Local


class Command(BaseCommand):
    help = 'Prepara cadastros de demonstração sem contas, senhas padrão ou autoria de relatos.'

    @transaction.atomic
    def handle(self, *args, **options):
        laboratorio, _ = Laboratorio.objects.get_or_create(codigo='DEMO', defaults={'nome': 'Laboratório de demonstração'})
        for numero in (1, 2):
            local, _ = Local.objects.get_or_create(laboratorio=laboratorio, nome=f'Bancada {numero:02d}')
            Equipamento.objects.get_or_create(
                codigo_patrimonio=f'DEMO-{numero:03d}',
                defaults={
                    'nome': f'Computador de demonstração {numero}',
                    'descricao': f'Computador para demonstração na bancada {numero:02d}',
                    'local': local,
                },
            )
        for nome in [
            'Não liga', 'Sem internet', 'Lentidão', 'Periférico', 'Software',
            'Monitor', 'Teclado/mouse', 'Áudio', 'Impressora',
        ]:
            Tag.objects.get_or_create(nome=nome)
        Tag.objects.get_or_create(outro=True, defaults={'nome': 'Outro problema'})
        self.stdout.write(self.style.SUCCESS('Cadastros preparados. Crie contas e atribua permissões pelo Admin.'))
