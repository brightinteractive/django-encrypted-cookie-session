DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'encrypted_cookies',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'p9m**y=lhm^j7o#kw!##1zaj-od^j2dl!b^ot3l+i!5)*24-p8'
