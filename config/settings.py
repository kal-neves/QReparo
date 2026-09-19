import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY no ambiente ou no arquivo .env.')

DEBUG = os.environ.get('DJANGO_DEBUG', 'false').lower() == 'true'

ALLOWED_HOSTS = [
    nome.strip() for nome in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if nome.strip()
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'equipamentos.apps.EquipamentosConfig',
    'chamados.apps.ChamadosConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'qreparo'),
        'USER': os.environ.get('POSTGRES_USER', 'qreparo'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Bahia'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MIDIA_PRIVADA = Path(os.environ.get('MIDIA_PRIVADA', BASE_DIR / 'midia_privada'))

FORMATOS_FOTO = ('png', 'jpg', 'jpeg', 'heic')
LIMITE_FOTOS = 2
FOTO_MAX_BYTES = 10_000_000
FOTO_ALVO_BYTES = 1_000_000
LIMITE_NAVEGADOR = 3
LIMITE_EQUIPAMENTO = 5
JANELA_MIN = 15
BLOQUEIO_MIN = 15
ABUSO_HORAS = 24
COOKIE_DIAS = 30
RETENCAO_AUX_DIAS = 30
RETENCAO_CANCELADO_DIAS = 14
RETENCAO_RESOLVIDO_MESES = 2
MENSAGEM_LIMITE = 'Muitos envios em pouco tempo. Tente novamente em alguns minutos.'
PRIORIDADES = ('Baixa', 'Média', 'Alta', 'Crítica')
TAGS_INICIAIS = (
    'não liga',
    'sem internet',
    'lentidão',
    'periférico',
    'software',
    'monitor',
    'teclado/mouse',
    'áudio',
    'impressora',
    'outro',
)


MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
