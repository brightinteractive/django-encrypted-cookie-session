Django Encrypted Session Cookie
===============================

Out of the box Django lets you run sessions with
[signed cookies](https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions).
This is nice because it relieves stress on your server.
However, you will need to be careful about what you store in your session since
a malicious user can read (but not alter) the values.

This module is an extension to signed cookies that encrypts the cookie value
so you don't have to think and worry about what sensitive data you might be
handing to the client.

**Author:** Francis Devereux, [Bright Interactive][1].

Adding it to your Django Project
================================

Here are some installation commands you can follow using the
[pip](http://www.pip-installer.org/) installer.
You'll need
[Django](https://djangoproject.com/) 1.4.x or greater (tested through 1.8)
and [cryptography](https://cryptography.io/en/latest/)
which are both automatically installed for you.
Python 2.6 or higher is supported but Python 3 is untested.

Install the module and its dependencies with pip:

    pip install django-encrypted-cookie-session

If you have any trouble with the cryptography module, read through
their [installation docs](https://cryptography.io/en/latest/installation/)
for tips.

Activate the session engine by putting this in your Django settings:

    SESSION_ENGINE = 'encrypted_cookies'

When you install `django-encrypted-cookie-session` you also get
the `encrypted-cookies-keygen` command. Run this to generate a key
to encrypt your cookies with:

    $ encrypted-cookies-keygen
    VDIXZGQS3fiJwG93Ha2jYZGZkxcqGDY3m-nZI3fha48=

Add it to your Django settings:

    ENCRYPTED_COOKIE_KEYS = ['VDIXZGQS3fiJwG93Ha2jYZGZkxcqGDY3m-nZI3fha48=']

Beware! If you don't use an HTTPS URL for local development
(you probably don't) then you may need to set this:

    SESSION_COOKIE_SECURE = False

Without it you might see a KeyError for session data because it
won't be saving properly. Obviously, in production where you use
an HTTPS URL you should make sure cookies are always secure.

Key Rotation
============

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

Cookie Size
===========

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

Logging
=======

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

Debugging
=========

If you need to debug an issue with sessions on a live system,
you can open a Python shell on the server and decrypt a cookie like this:

    from django.core import signing
    from encrypted_cookies import EncryptingPickleSerializer

    signing.loads("<cookie_value>", salt='encrypted_cookies', serializer=EncryptingPickleSerializer)

Writing Django Tests
====================

When writing [Django tests](https://docs.djangoproject.com/en/dev/topics/testing/)
for an application that uses encrypted cookie sessions
there are a few things to consider. If your view sets a session variable
and you want to check that value later in an assertion then it's no problem,
you can just access `self.client.session['the-thing']` as you'd expect.
However, if you need to set up a session *before* running view code
then you need to think like a cookie. Here's a way to prepare session
data for a view (tested in Django 1.8):

    # Imagine that this is inside a subclass of django.test.TestCase
    session = self.client.session  # activate Django's weird getter
    session['user_id'] = '<logged-in-user-id>'
    session.save()
    # Next, you'll need to load the encrypted session into a
    # request cookie so that the view will parse it.
    # The `session_key` is actually the session contents.
    self.client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    # Now when you run your view code it will see the session data:
    self.client.get('/some-login-protected-url')

Publishing releases to PyPI
===========================

To publish a new version of django-encrypted-cookie-session to PyPI, set the
`__version__` string in `encrypted_cookies/__init__.py`, then run:

    # Run the tests against multiple environments
    tox
    # Publish to PyPI
    ./setup.py publish
    # Tag (change 1.0.0 to the version you are publishing!)
    git tag -a v1.0.0 -m 'Version 1.0.0'
    git push --tags


Running the tests
=================

To run the tests against multiple environments, install
[tox](http://tox.readthedocs.org/) using
`pip install tox`. You need at least Python 2.7 to run tox itself but you'll
need 2.6 as well to run all environments. Run the tests like this:

    tox

If you are running on OS X and have OpenSSL installed in MacPorts then you
may need to run tox with the environment variables suggested by
https://cryptography.io/en/latest/installation/#using-your-own-openssl-on-os-x
like this:

    env ARCHFLAGS="-arch x86_64" LDFLAGS="-L/opt/local/lib" CFLAGS="-I/opt/local/include" tox

To run the tests against a single environment:

    tox -e py27-django18

To debug something weird, run it directly from the virtualenv like:

    .tox/py27-django18/bin/python manage.py test

Changelog
=========

3.0.0
-----

* Dropped support for [M2Crypto](https://pypi.python.org/pypi/M2Crypto)
  in favor of [cryptography](https://cryptography.io/en/latest/) for
  better platform support.
* **BREAKING CHANGE**: Old values from the `ENCRYPTED_COOKIE_KEY` setting
  no longer work because key formatting changed. You must generate a new
  key with the provided command and define it in the list setting like
  `ENCRYPTED_COOKIE_KEYS = [...]`.
* **BREAKING CHANGE**: The Django `SECRET_KEY` setting can no longer be
  used as a fallback. Define `ENCRYPTED_COOKIE_KEYS = [...]` instead.
* Removed support for
  [django-paranoia](https://django-paranoia.readthedocs.org/en/latest/)
  because its core features are included with Django now.

2.0.0
-----

* Drop support for pycrypto to fix
  https://github.com/brightinteractive/django-encrypted-cookie-session/issues/11
  and
  https://github.com/brightinteractive/django-encrypted-cookie-session/issues/12

1.1.1
-----

* Fix ImportError with Django 1.5.3+

1.1.0
-----

* Added optional `ENCRYPTED_COOKIE_KEY` in addition to `SECRET_KEY` to encourage
  care and isolation of the key. You do not need to add `ENCRYPTED_COOKIE_KEY` to
  your settings unless you want to.
* Extended django-paranoia (optional)
* Added optional support for M2Crypto and m2secret
* Added support for Python 2.6, Python 2.7, and Django 1.5
* Added more test coverage
* Compress cookie value before encrypting

1.0.0
-----

* Initial release

License
=======

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
