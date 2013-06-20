DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'encrypted_cookies',
)

MIDDLEWARE_CLASSES = (
    'django_paranoia.middleware.Middleware',
)

# Pretend this is a random, secure key you created that was
# longer than 32 characters.
ENCRYPTED_COOKIE_KEY = 'p9m**y=lhm^j7o#kw!##1zaj-od^j2dl!b^ot3l+i!5)*24-p8'

SECRET_KEY = 'stub-value-for-django'
