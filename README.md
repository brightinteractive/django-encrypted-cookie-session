Django Encrypted Session Cookie
===============================

**Encrypted cookie session backend.**

**Author:** Francis Devereux, [Bright Interactive][1].

Adding to your Django Project
=============================

This requires Django 1.4.x,
[M2Crypto](https://pypi.python.org/pypi/M2Crypto),
[m2secret](https://pypi.python.org/pypi/m2secret), and
[django-paranoia][2]. The dependencies will be installed automatically.

Install it with [pip](http://www.pip-installer.org/):

    pip install django-encrypted-cookie-session

Activate the session engine by putting this in your Django settings:

    SESSION_ENGINE = 'encrypted_cookies'

Add a strong random key to use for encryption. Make sure it is at least 32
characters long and instead of banging on your keyboard take care to make sure
it is really random. You should change this key periodically.

    ENCRYPTED_COOKIE_KEY = 'really-long-random-string'

Make sure [django-paranoia][2] middleware is installed in settings:

    MIDDLEWARE_CLASSES = (
        ...
        'django_paranoia.middleware.Middleware',
    )

You may also want to hook up the reporters:

    DJANGO_PARANOIA_REPORTERS = [
        'django_paranoia.reporters.log',
    ]


Publishing releases to PyPI
===========================

To publish a new version of django-validate-on-save to PyPI, set the
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

To run the tests against multiple environments, install `tox` using
`pip install tox`. You need at least Python 2.7 to run tox itself but you'll
need 2.6 as well to run all environments. Run the tests like this:

    tox

To run the tests against a single environment:

    tox -e py27-django15

To debug something weird, run it directly from the virtualenv like:

    .tox/py27-django15/bin/python manage.py test

Changelog
=========

1.1.0
-----

* Switched to ENCRYPTED_COOKIE_KEY instead of SECRET_KEY to encourage care and
  isolation of the key. You need to add ENCRYPTED_COOKIE_KEY to your settings.
* Extended django-paranoia
* Switched to M2Crypto and m2secret
* Added support for Python 2.6, Python 2.7, and Django 1.5
* Added more test coverage

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
[2]: https://pypi.python.org/pypi/django-paranoia
