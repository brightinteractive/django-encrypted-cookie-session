# Django Encrypted Session Cookie

Out of the box Django lets you run sessions with
[signed cookies](https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions).
This is nice because it relieves stress on your server.
However, you will need to be careful about what you store in your session since
a malicious user can read (but not alter) the values.

This module is an extension to signed cookies that encrypts the cookie value
so you don't have to think and worry about what sensitive data you might be
handing to the client.

**Author:** Francis Devereux, [Bright Interactive][1].

# Adding it to your Django Project

You'll need
[Django](https://djangoproject.com/) 1.4.x or greater (tested through 1.8)
and
Python 2.6 or higher. Python 3 is currently untested.
You'll also need to install a backend for the actual cryptographic operations.
See the section on backends for their respective installation instructions.

Install the module and its dependencies with [pip](http://www.pip-installer.org/):

    pip install django-encrypted-cookie-session

Activate the session engine by putting this in your Django settings:

    SESSION_ENGINE = 'encrypted_cookies'

See the instructions on your chosen backend for how to configure
your `ENCRYPTED_COOKIE_KEYS` setting.

Beware! If you don't use an HTTPS URL for local development
(you probably don't) then you may need to set this:

    SESSION_COOKIE_SECURE = False

Without it you might see a KeyError for session data because it
won't be saving properly. Obviously, in production where you use
an HTTPS URL you should make sure cookies are always secure.

# Crypto Backends

The following are the available backends you can use for
cryptographic operations. You need to install at least one.

## Cryptography

### Installation and configuration

The [cryptography](https://cryptography.io/en/latest/) backend
is the default. Install it with pip like this:

    pip install 'cryptography>=0.7'

You can explicitly activate it with this setting:

    ENCRYPTED_COOKIE_BACKEND = 'cryptography'

When you install `django-encrypted-cookie-session` you also get
the `encrypted-cookies-keygen` command. Run this to generate a key
to encrypt your cookies with:

    $ encrypted-cookies-keygen
    VDIXZGQS3fiJwG93Ha2jYZGZkxcqGDY3m-nZI3fha48=

Add it to your Django settings:

    ENCRYPTED_COOKIE_KEYS = ['VDIXZGQS3fiJwG93Ha2jYZGZkxcqGDY3m-nZI3fha48=']

### Key Rotation

For added protection, you can rotate your encryption keys whenever
you like. When you add a new key, you may wish to include the old
key temporarily so that any sessions active during your deployment
will not be reset.

Add the *new* key first in the list like this:

    ENCRYPTED_COOKIE_KEYS = [
        # New key:
        '9evXbsR_1yZA5EW_blSI4O69MjGKwOu1-UwLK_PWyKw=',
        # Old key:
        'VDIXZGQS3fiJwG93Ha2jYZGZkxcqGDY3m-nZI3fha48=',
    ]

Any time a user makes a request to a Django view that alters the session,
the cookie will be re-encrypted in the response.
Thus, you can safely remove old keys soon after you deploy a new key.

## M2Crypto

### Installation and Configuration

[M2Crypto](https://github.com/martinpaljak/M2Crypto/)
requires [swig](http://www.swig.org/)
so first you need to install that with your
package manager. On Mac OS X with [homebrew](http://brew.sh/) you can do:

    brew install swig

At the time of this writing, there is an
[open bug](https://github.com/martinpaljak/M2Crypto/issues/60)
which may require you to downgrade swig or downgrade M2Crypto.
Version 0.22.1 of M2Crypto is known to work.
Say a prayer and try to install it:

    pip install 'M2Crypto>=0.22.1'

Activate the backend with this setting:

    ENCRYPTED_COOKIE_BACKEND = 'M2Crypto'

Think of a long secret (preferably longer than 32 bytes)
and add it to your Django settings:

    ENCRYPTED_COOKIE_KEYS = ['some really long secret']

### Key Rotation

Key rotation is not currently supported in the M2Crypto backend.

# Cookie Size

Most browsers limit cookie size to 4092 bytes (name + value).
Most servers also have a limit to the request/response header size
they can process.
It's pretty easy to hit these limits since an encrypted cookie takes all
sesssion data, serializes it, and encrypts it. You can compress the value
(using
[zlib](http://docs.python.org/2/library/zlib.html#module-zlib))
with this setting:

    COMPRESS_ENCRYPTED_COOKIE = True

The default compression level is 6 but you can adjust that for speed/accuracy
like this:

    ENCRYPTED_COOKIE_COMPRESSION_LEVEL = 1

Also note that the cookie value will be sent to your server on every request so
size may also affect network performance. For best results, limit the amount of
data you store in the session. If you turn on logging, you'll see the byte size
of each session cookie.

# Logging

This module outputs some logging in the `encrypted_cookies` channel.
Here is a settings example for enabling logging in Django:

    LOGGING = {
        'loggers': {
            'encrypted_cookies': {
                'level': logging.INFO,
                'handlers': ['console']
            }
        }
    }

# Debugging

If you need to debug an issue with sessions on a live system,
you can open a Python shell on the server and decrypt a cookie like this:

    from django.core import signing
    from encrypted_cookies import EncryptingPickleSerializer

    signing.loads("<cookie_value>", salt='encrypted_cookies', serializer=EncryptingPickleSerializer)


# Publishing releases to PyPI

To publish a new version of django-validate-on-save to PyPI, set the
`__version__` string in `encrypted_cookies/__init__.py`, then run:

    # Run the tests against multiple environments
    tox
    # Publish to PyPI
    ./setup.py publish
    # Tag (change 1.0.0 to the version you are publishing!)
    git tag -a v1.0.0 -m 'Version 1.0.0'
    git push --tags


# Running the tests

To run the tests against multiple environments, install
[tox](http://tox.readthedocs.org/) using
`pip install tox`. You need at least Python 2.7 to run tox itself but you'll
need 2.6 as well to run all environments. Run the tests like this:

    tox

To run the tests against a single environment:

    tox -e py27-django18

To debug something weird, run it directly from the virtualenv like:

    .tox/py27-django18/bin/python manage.py test

If you are having trouble with the cryptography module, see the
[installation docs](https://cryptography.io/en/latest/installation/) for tips.
You may need to specify your openssl path.

# Changelog

## 3.0.0

* Added configurable backends.
* Added support for [cryptography](https://cryptography.io/en/latest/).
* **BREAKING CHANGE**: `cryptography` is the default backend so if you
  want your old configuration to "just work" you need to set
  `ENCRYPTED_COOKIE_BACKEND = 'M2Crypto'`.
* **BREAKING CHANGE**: Removed support for
  [django-paranoia](https://django-paranoia.readthedocs.org/en/latest/)
  because its core features are included with Django now.
* **DEPRECATED**: to prepare for key rotation, the `ENCRYPTED_COOKIE_KEY`
  setting is deprecated in favor or `ENCRYPTED_COOKIE_KEYS = [...]`.
* **DEPRECATED**: falling back to the Django `SECRET_KEY` setting is
  deprecated. Define `ENCRYPTED_COOKIE_KEYS = [...]` instead.
* Updated tests to cover Django through version 1.8.

## 2.0.0

* Drop support for pycrypto to fix
  https://github.com/brightinteractive/django-encrypted-cookie-session/issues/11
  and
  https://github.com/brightinteractive/django-encrypted-cookie-session/issues/12

## 1.1.1

* Fix ImportError with Django 1.5.3+

## 1.1.0

* Added optional `ENCRYPTED_COOKIE_KEY` in addition to `SECRET_KEY` to encourage
  care and isolation of the key. You do not need to add `ENCRYPTED_COOKIE_KEY` to
  your settings unless you want to.
* Extended django-paranoia (optional)
* Added optional support for M2Crypto and m2secret
* Added support for Python 2.6, Python 2.7, and Django 1.5
* Added more test coverage
* Compress cookie value before encrypting

## 1.0.0

* Initial release

# License

Copyright (c) Bright Interactive Limited.
Started with django-reusable-app Copyright (c) DabApps.

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

[1]: http://www.bright-interactive.com/
