import os
from decouple import Csv
from dj_database_url import parse as dburl
from djangosige import __version__
from .configs import DEFAULT_DATABASE_URL, DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS
from .runtime import (
    build_database_url,
    env_bool,
    project_config,
    read_env_file,
    resolve_env_path,
    resolve_runtime_paths,
)

APP_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(APP_ROOT))
ENV_PATH = resolve_env_path(PROJECT_ROOT, os.environ)
PROJECT_ENV = read_env_file(ENV_PATH)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = project_config(PROJECT_ENV, os.environ, 'SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool(PROJECT_ENV, os.environ, 'DEBUG', default=False)

ALLOWED_HOSTS = project_config(PROJECT_ENV, os.environ, 'ALLOWED_HOSTS', default='', cast=Csv())

APP_DISPLAY_NAME = project_config(PROJECT_ENV, os.environ, 'APP_DISPLAY_NAME', default='DevLab ERP')
APP_BRAND_PRIMARY = project_config(PROJECT_ENV, os.environ, 'APP_BRAND_PRIMARY', default='DevLab')
APP_BRAND_ACCENT = project_config(PROJECT_ENV, os.environ, 'APP_BRAND_ACCENT', default='SIGE')
APP_TAGLINE = project_config(PROJECT_ENV, os.environ, 'APP_TAGLINE', default='Sistema integrado de gestao.')
APP_VERSION = project_config(PROJECT_ENV, os.environ, 'APP_VERSION', default=__version__)
APP_COPYRIGHT_START_YEAR = project_config(PROJECT_ENV, os.environ, 'APP_COPYRIGHT_START_YEAR', default='2017')
APP_DOCS_URL = project_config(PROJECT_ENV, os.environ, 'APP_DOCS_URL', default='https://instagram.com/leonardovieira.sh')
CNPJ_LOOKUP_URL_TEMPLATE = project_config(PROJECT_ENV, os.environ, 'CNPJ_LOOKUP_URL_TEMPLATE', default='https://brasilapi.com.br/api/cnpj/v1/{cnpj}')
CNPJ_LOOKUP_TIMEOUT = project_config(PROJECT_ENV, os.environ, 'CNPJ_LOOKUP_TIMEOUT', default='8', cast=int)

if not DEFAULT_DATABASE_URL:
    DEFAULT_DATABASE_URL = ''

RUNTIME_PATHS = resolve_runtime_paths(PROJECT_ROOT, APP_ROOT, PROJECT_ENV, os.environ)
APP_DATA_ROOT = RUNTIME_PATHS['APP_DATA_ROOT']
LOG_ROOT = RUNTIME_PATHS['LOG_ROOT']
DATABASE_URL = build_database_url(DEFAULT_DATABASE_URL, APP_DATA_ROOT, PROJECT_ENV, os.environ)

DATABASES = {
    'default': dburl(DATABASE_URL),
}


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # djangosige apps:
    'djangosige.apps.base',
    'djangosige.apps.login',
    'djangosige.apps.cadastro',
    'djangosige.apps.vendas',
    'djangosige.apps.compras',
    'djangosige.apps.fiscal',
    'djangosige.apps.financeiro',
    'djangosige.apps.estoque',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware para paginas que exigem login
    'djangosige.middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'djangosige.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(APP_ROOT, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # contexto para a versao do sige
                'djangosige.apps.base.context_version.sige_version',
                # contexto para shell principal
                'djangosige.apps.base.context_shell.shell_navigation',
                # contexto para a foto de perfil do usuario
                'djangosige.apps.login.context_user.foto_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangosige.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'pt-br'

#TIME_ZONE = 'UTC'
TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = RUNTIME_PATHS['STATIC_ROOT']

STATICFILES_DIRS = [
    os.path.join(APP_ROOT, 'static'),
]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG else
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

FIXTURE_DIRS = [
    os.path.join(APP_ROOT, 'fixtures'),
]

MEDIA_ROOT = RUNTIME_PATHS['MEDIA_ROOT']
MEDIA_URL = '/media/'

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_NOT_REQUIRED = (
    r'^/login/$',
    r'^/login/consultacnpj/$',
    r'^/healthz/$',
    r'/login/esqueceu/',
    r'/login/trocarsenha/',
    r'/logout/',
)
