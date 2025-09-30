import os
from pathlib import Path

from dotenv import load_dotenv
from split_settings.tools import include

dotenv_path = os.path.join(os.path.dirname(__file__), '../.env.dev')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', False) == 'True'

ALLOWED_HOSTS = (os.environ.get('ALLOWED_HOSTS') or '').split(',')

CSRF_TRUSTED_ORIGINS = (os.environ.get('CSRF_TRUSTED_ORIGINS') or '').split(',')

# Загружаем настройки из модулей
include(
    'components/application.py',
    'components/middleware.py',
    'components/templates.py',
    'components/database.py',
    'components/auth.py',
    'components/static.py',
    'components/drf.py',
    'components/jwt.py',
)

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

NOTIFY_SERVICE_URL = os.getenv("NOTIFY_SERVICE_URL", "")