import base64
from io import BytesIO
from urllib.parse import urlsplit

import qrcode
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


def url_do_relato(equipamento):
    origem = settings.QREPARO_PUBLIC_URL.rstrip('/')
    partes = urlsplit(origem)
    if (
        partes.scheme not in ('http', 'https') or not partes.netloc
        or partes.path or partes.query or partes.fragment or partes.username or partes.password
    ):
        raise ImproperlyConfigured('configure QREPARO_PUBLIC_URL com a origem pública da aplicação')
    return origem + reverse('paginas:relato', kwargs={'token': equipamento.qr_token})


def gerar_qr(url):
    imagem = qrcode.make(url)
    arquivo = BytesIO()
    imagem.save(arquivo, format='PNG')
    conteudo = base64.b64encode(arquivo.getvalue()).decode('ascii')
    return f'data:image/png;base64,{conteudo}'
