# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x_spxq%tc#z(dv6_u5bg$t10(=6w0a(*f1$=%8rydn8lndaj+8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.openid',
    'widget_tweaks',
    'captcha',
    'LedenAdministratie'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

SITE_ID=2

ROOT_URLCONF = 'LedenAdministratie.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)


LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/ledenlijst/'
ACCOUNT_LOGIN_REDIRECT_URL='/ledenlijst/'
ACCOUNT_EMAIL_VERIFICATION='none'
ACCOUNT_AUTHENTICATION_METHOD='username'
ACCOUNT_DEFAULT_HTTP_PROTOCOL='https'
ACCOUNT_SESSION_REMEMBER=False
SOCIALACCOUNT_QUERY_EMAIL=True


EMAIL_HOST="mail.rmoesbergen.nl"
EMAIL_PORT=587
EMAIL_HOST_USER='mail@rmoesbergen.nl'
EMAIL_HOST_PASSWORD='lMDgR4PiY6yDkLPc'
EMAIL_SENDER='mail@rmoesbergen.nl'
EMAIL_USE_TLS=True
EMAIL_RECIPIENTS_UPDATE=['mail@rmoesbergen.nl']
EMAIL_RECIPIENTS_NEW=['mail@rmoesbergen.nl']
SEND_UPDATE_EMAILS=True


WSGI_APPLICATION = 'LedenAdministratie.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'nl-nl'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/srv/media'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

