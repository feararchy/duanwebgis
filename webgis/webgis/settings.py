"""
Django settings for webgis project.
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o6)@3v*_yt7i$#sy$&d09ry2s#b7lzyzz27hg-una8+d28&a)p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- THƯ VIỆN BỔ SUNG ---
    'django.contrib.humanize', # Định dạng tiền tệ
    
    # --- APP CỦA BẠN ---
    'nhomgis',
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

ROOT_URLCONF = 'webgis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Trỏ vào thư mục templates gốc
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

WSGI_APPLICATION = 'webgis.wsgi.application'


# Database
# Cấu hình PostgreSQL (Đã xóa SQLite đi để tránh xung đột)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'webgis_db',      # Tên DB bạn tạo trong pgAdmin
        'USER': 'postgres',       # User mặc định
        'PASSWORD': '1',          # Mật khẩu của bạn
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# Tắt kiểm tra mật khẩu phức tạp để dễ test (nhập 123456 cho nhanh)
AUTH_PASSWORD_VALIDATORS = []


# Internationalization

LANGUAGE_CODE = 'vi-vn' # Đổi sang tiếng Việt cho dễ nhìn

TIME_ZONE = 'Asia/Ho_Chi_Minh' # Múi giờ Việt Nam

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'

# Cấu hình thư mục static gốc (nơi chứa css, js chung)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'