import dj_database_url
from urllib.parse import urlsplit

from .settings import *


if DEBUG:
    raise ImproperlyConfigured('Use DJANGO_DEBUG=false na hospedagem.')
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:
    raise ImproperlyConfigured('Use uma DJANGO_SECRET_KEY aleatória de pelo menos 50 caracteres.')
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Defina DJANGO_ALLOWED_HOSTS com os domínios da aplicação.')

ALLOWED_HOSTS = [*ALLOWED_HOSTS, 'healthcheck.railway.app']
origem = urlsplit(QREPARO_PUBLIC_URL)
if (origem.scheme != 'https' or not origem.hostname or origem.path not in ('', '/')
        or origem.query or origem.fragment or origem.username or origem.password
        or origem.hostname not in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Defina QREPARO_PUBLIC_URL como origem HTTPS de um host permitido.')
QREPARO_PUBLIC_URL = QREPARO_PUBLIC_URL.rstrip('/')
CSRF_TRUSTED_ORIGINS = [QREPARO_PUBLIC_URL]

url_banco = os.environ.get('DATABASE_URL', '')
if urlsplit(url_banco).scheme not in ('postgres', 'postgresql'):
    raise ImproperlyConfigured('Defina DATABASE_URL com a conexão PostgreSQL da hospedagem.')
try:
    banco = dj_database_url.parse(url_banco, conn_max_age=60, conn_health_checks=True)
except (ValueError, KeyError) as erro:
    raise ImproperlyConfigured('DATABASE_URL inválida.') from erro
if not banco.get('HOST') or not banco.get('NAME'):
    raise ImproperlyConfigured('DATABASE_URL deve informar host e banco.')
banco.setdefault('OPTIONS', {}).setdefault('connect_timeout', 5)
DATABASES = {'default': banco}

raiz_fotos = os.environ.get('QREPARO_FOTOS_ROOT', '')
if not raiz_fotos or not Path(raiz_fotos).is_absolute():
    raise ImproperlyConfigured('Defina QREPARO_FOTOS_ROOT como caminho absoluto dentro do volume.')
QREPARO_FOTOS_ROOT = Path(raiz_fotos).resolve()
for publica in (STATIC_ROOT, BASE_DIR / 'static', BASE_DIR / 'assets'):
    publica = Path(publica).resolve()
    if QREPARO_FOTOS_ROOT.is_relative_to(publica) or publica.is_relative_to(QREPARO_FOTOS_ROOT):
        raise ImproperlyConfigured('A pasta privada deve ficar separada dos arquivos estáticos.')

MIDDLEWARE = [MIDDLEWARE[0], 'whitenoise.middleware.WhiteNoiseMiddleware', *MIDDLEWARE[1:]]
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r'^saude/$']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
# Hospedagem temporária: não comprometer subdomínios nem solicitar preload.
# As demais advertências de deploy continuam interrompendo a inicialização.
SILENCED_SYSTEM_CHECKS = ['security.W005', 'security.W021']
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
