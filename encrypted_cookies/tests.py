# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com

from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
try:
    from django.utils.six.moves import cStringIO as StringIO
except ImportError:
    # For Django < 1.5:
    from cStringIO import StringIO

from cryptography.fernet import Fernet
try:
    from unittest import mock
except ImportError:
    # For Python < 3.3
    import mock

from encrypted_cookies import (
    keygen,
    EncryptingPickleSerializer,
    SessionStore,
)


@override_settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()])
class Base(TestCase):
    pass


class EncryptionTests(Base):

    def setUp(self):
        self.pkl = EncryptingPickleSerializer()

    @override_settings(ENCRYPTED_COOKIE_KEYS=None)
    def test_empty_key_not_allowed(self):
        with self.assertRaises(ImproperlyConfigured):
            self.pkl.dumps('summat')

    def test_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted.decode('ascii'))
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    @override_settings(ENCRYPTED_COOKIE_KEYS=['nope'])
    def test_incorrect_key_value(self):
        with self.assertRaises(ValueError):
            self.pkl.dumps('summat')

    @override_settings(COMPRESS_ENCRYPTED_COOKIE=True)
    def test_compressed_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted.decode('ascii'))
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    def test_recover_from_uncompressed_value(self):
        plaintext_bytes = 'adsfasdfw34wras'
        with override_settings(COMPRESS_ENCRYPTED_COOKIE=False):
            encrypted = self.pkl.dumps(plaintext_bytes)
        with override_settings(COMPRESS_ENCRYPTED_COOKIE=True):
            # Make sure this doesn't raise an exception.
            decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)


class SessionStoreTests(Base):

    def setUp(self):
        req = RequestFactory().get('/')
        req.META['REMOTE_ADDR'] = '10.0.0.1'
        self.sess = SessionStore()

    def test_save_load(self):
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        self.assertEqual(stor['secret'], 'laser beams')

    def test_wrong_key(self):
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()]):
            self.sess['secret'] = 'laser beams'
            self.sess.save()
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()]):
            stor = self.sess.load()

        # The decryption error is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    def test_key_rotation(self):
        key1 = Fernet.generate_key()

        with self.settings(ENCRYPTED_COOKIE_KEYS=[key1]):
            self.sess['secret'] = 'laser beams'
            self.sess.save()
        # Decrypt a value using an old key:
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key(),
                                                  key1]):
            stor = self.sess.load()

        self.assertEqual(dict(stor.items()), {'secret': 'laser beams'})

    @mock.patch('encrypted_cookies.signing.loads')
    def test_bad_signature(self, loader):
        loader.side_effect = signing.BadSignature
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        # The BadSignature error is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    @mock.patch('encrypted_cookies.signing.loads')
    def test_bad_signing_value(self, loader):
        loader.side_effect = ValueError
        self.sess['secret'] = 'laser beams'
        self.sess.save()
        stor = self.sess.load()
        # The ValueError is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

    @mock.patch('encrypted_cookies.EncryptingPickleSerializer')
    def test_use_encrypted_pickles(self, PicklerClass):
        pickler = mock.Mock()
        PicklerClass.return_value = pickler
        pickler.dumps.return_value = b'<data>'

        self.sess.save()
        self.sess.load()

        # Because there is multiple inheritance going on now, make
        # sure that the encrypted pickler is used.
        assert pickler.dumps.called
        assert pickler.loads.called


class TestKeygen(TestCase):

    def test_generate_key(self):
        stdout = StringIO()
        try:
            keygen.main(stdout=stdout, argv=[])
        except SystemExit as exc:
            self.assertEqual(exc.code, 0)

        key = stdout.getvalue()
        f = Fernet(key)
        # Make sure this doesn't raise an error about a bad key.
        f.decrypt(f.encrypt(b'whatever'))
