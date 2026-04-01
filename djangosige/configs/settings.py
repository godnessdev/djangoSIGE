import os
from decouple import Csv
from dj_database_url import parse as dburl
from .configs import DEFAULT_DATABASE_URL, DEFAULT_FROM_EMAIL, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_PORT, EMAIL_USE_TLS

APP_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(APP_ROOT))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
PROJECT_ENV = {}

if os.path.exists(ENV_PATH):
    with open(ENV_PATH, encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            PROJECT_ENV[key.strip()] = value.strip()


def project_config(name, default=None, cast=None):
    if name in PROJECT_ENV:
        value = PROJECT_ENV[name]
    elif name in os.environ:
        value = os.environ[name]
    else:
        value = default

    if cast is None:
        return value

    return cast(value)


def env_bool(name, default=False):
    value = project_config(name, default=str(default))
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = project_config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool('DEBUG', default=False)

ALLOWED_HOSTS = project_config('ALLOWED_HOSTS', default='', cast=Csv())

if not DEFAULT_DATABASE_URL:
    DEFAULT_DATABASE_URL = 'sqlite:///' + os.path.join(APP_ROOT, 'db.sqlite3')

DATABASES = {
    'default': project_config('DATABASE_URL', default=DEFAULT_DATABASE_URL, cast=dburl),
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
STATIC_ROOT = os.path.join(APP_ROOT, 'staticfiles')

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

MEDIA_ROOT = os.path.join(APP_ROOT, 'media/')
MEDIA_URL = 'media/'

SESSION_EXPIRE_AT_BROWSER_CLOSE = False

LOGIN_NOT_REQUIRED = (
    r'^/login/$',
    r'/login/esqueceu/',
    r'/login/trocarsenha/',
    r'/logout/',
)
