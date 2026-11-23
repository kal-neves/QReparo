import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from chamados.models import Foto


class Command(BaseCommand):
    help = 'Verifica conexão, volume persistente e, opcionalmente, arquivos referenciados no banco.'

    def add_arguments(self, parser):
        parser.add_argument('--fotos', action='store_true', help='Confere a presença e o tamanho dos anexos cadastrados.')

    def handle(self, *args, **options):
        montagem = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '')
        if not montagem or not Path(montagem).is_absolute() or not Path(montagem).is_dir():
            raise CommandError('Volume ausente: confira RAILWAY_VOLUME_MOUNT_PATH e a montagem no serviço.')
        raiz = Path(settings.QREPARO_FOTOS_ROOT).resolve()
        volume = Path(montagem).resolve()
        if raiz == volume or not raiz.is_relative_to(volume):
            raise CommandError('QREPARO_FOTOS_ROOT deve ser uma subpasta do volume persistente.')
        try:
            raiz.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(dir=raiz, prefix='.verificacao-') as arquivo:
                arquivo.write(b'qreparo')
                arquivo.flush()
                arquivo.seek(0)
                if arquivo.read() != b'qreparo':
                    raise OSError
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        except (OSError, DatabaseError) as erro:
            raise CommandError('Falha na conexão ou na leitura/escrita do volume.') from erro
        if options['fotos']:
            falhas = 0
            for foto in Foto.objects.iterator():
                try:
                    if foto.arquivo.size != foto.tamanho:
                        falhas += 1
                except OSError:
                    falhas += 1
            if falhas:
                raise CommandError(f'{falhas} foto(s) ausente(s) ou com tamanho divergente. Confira o backup correspondente.')
            self.stdout.write('Anexos cadastrados encontrados com os tamanhos esperados.')
        self.stdout.write(self.style.SUCCESS('Conexão e volume verificados.'))
