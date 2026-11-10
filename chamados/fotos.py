import logging
import warnings
from pathlib import Path
from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener


register_heif_opener()
LIMITE_FOTO = 10_000_000
LIMITE_ENVIO = 25_000_000
logger = logging.getLogger(__name__)


class ArmazenamentoPrivado(FileSystemStorage):
    @property
    def base_location(self):
        return str(settings.QREPARO_FOTOS_ROOT)

    @property
    def location(self):
        return str(Path(self.base_location).resolve())

    def url(self, name):
        raise ValueError('Fotos privadas não possuem URL pública.')


def armazenamento_fotos():
    return ArmazenamentoPrivado()


def caminho_foto(instance, filename):
    return f'fotos/{uuid4().hex}.webp'


def arquivos_do_envio(request):
    if any(campo != 'fotos' for campo in request.FILES):
        raise ValidationError('Envie os anexos no campo fotos.')
    return request.FILES.getlist('fotos')


def preparar_fotos(arquivos):
    arquivos = list(arquivos)
    if len(arquivos) > 2:
        raise ValidationError('Envie no máximo duas fotos.')
    return [preparar_foto(arquivo) for arquivo in arquivos]


def preparar_foto(arquivo):
    if arquivo.size > LIMITE_FOTO:
        raise ValidationError('Cada foto deve ter no máximo 10 MB.')
    arquivo.seek(0)
    dados = arquivo.read(LIMITE_FOTO + 1)
    if len(dados) > LIMITE_FOTO:
        raise ValidationError('Cada foto deve ter no máximo 10 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(dados)) as origem:
                if origem.format not in {'PNG', 'JPEG', 'HEIF'}:
                    raise ValidationError('Envie fotos PNG, JPEG ou HEIC.')
                origem.load()
                orientada = ImageOps.exif_transpose(origem)
                modo = 'RGBA' if orientada.has_transparency_data else 'RGB'
                convertida = orientada.convert(modo)
                limpa = Image.new(modo, convertida.size)
                limpa.paste(convertida)
                for qualidade in (85, 75, 65):
                    saida = BytesIO()
                    limpa.save(saida, format='WEBP', quality=qualidade, method=4)
                    if saida.tell() <= 1_000_000:
                        break
                return ContentFile(saida.getvalue()), limpa.width, limpa.height
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as erro:
        raise ValidationError('Foto inválida ou impossível de processar. Envie outra imagem.') from erro


def apagar_arquivo(storage, nome):
    try:
        storage.delete(nome)
    except OSError:
        logger.error('Falha ao remover arquivo privado de foto.')
