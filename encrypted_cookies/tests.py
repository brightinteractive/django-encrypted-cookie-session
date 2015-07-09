# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
import cStringIO

from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
try:
    from django.test.utils import skipUnless
except ImportError:
    # For Django < 1.6:
    from django.utils.unittest.case import skipUnless

from cryptography.fernet import Fernet
import mock

from encrypted_cookies import (
    crypto,
    keygen,
    EncryptingPickleSerializer,
    SessionStore,
)


@override_settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()])
class Base(TestCase):
    pass


class CookieEncryptionTests(Base):

    def setUp(self):
        self.pkl = EncryptingPickleSerializer()

    def test_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted)
        decrypted = self.pkl.loads(encrypted)
        self.assertEqual(plaintext_bytes, decrypted)

    def test_default_backend(self):
        backend = crypto.get_backend()
        self.assertEqual(backend.module_name, 'cryptography')

    @override_settings(ENCRYPTED_COOKIE_BACKEND='nopenotreally')
    def test_unknown_backend(self):
        with self.assertRaises(ImproperlyConfigured):
            crypto.get_backend()

    @override_settings(COMPRESS_ENCRYPTED_COOKIE=True)
    def test_compressed_encrypt_decrypt(self):
        plaintext_bytes = 'adsfasdfw34wras'
        encrypted = self.pkl.dumps(plaintext_bytes)
        self.assertNotEqual(plaintext_bytes, encrypted)
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

    def test_wrong_key_resets_session(self):
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()]):
            self.sess['secret'] = 'laser beams'
            self.sess.save()
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()]):
            stor = self.sess.load()

        # The decryption error is ignored and the session is reset.
        self.assertEqual(dict(stor.items()), {})

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
        pickler.dumps.return_value = '<data>'

        self.sess.save()
        self.sess.load()

        # Because there is multiple inheritance going on now, make
        # sure that the encrypted pickler is used.
        assert pickler.dumps.called
        assert pickler.loads.called


class TestKeygen(TestCase):

    def test_generate_key(self):
        stdout = cStringIO.StringIO()
        try:
            keygen.main(stdout=stdout, argv=[])
        except SystemExit, exc:
            self.assertEqual(exc.code, 0)

        key = stdout.getvalue()
        f = Fernet(key)
        # Make sure this doesn't raise an error about a bad key.
        f.decrypt(f.encrypt('whatever'))


class BackendTests(Base):

    def setUp(self):
        self.backend = crypto.get_backend()


@override_settings(ENCRYPTED_COOKIE_BACKEND='cryptography')
class CryptographyTests(BackendTests):

    def test_lookup(self):
        self.assertEqual(self.backend.module_name, 'cryptography')

    @override_settings(ENCRYPTED_COOKIE_KEYS=None)
    def test_empty_key_not_allowed(self):
        with self.assertRaises(ImproperlyConfigured):
            crypto.get_backend().encrypt('summat')

    def test_encrypt_decrypt(self):
        message = 'the house key is under the mat'
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key()]):
            token = self.backend.encrypt(message)
        self.assertEqual(self.backend.decrypt(token), message)

    @override_settings(ENCRYPTED_COOKIE_KEYS=['nope'])
    def test_incorrect_key_value(self):
        with self.assertRaises(ValueError):
            crypto.get_backend().encrypt('summat')

    @override_settings(ENCRYPTED_COOKIE_KEYS=None,
                       ENCRYPTED_COOKIE_KEY='some old key')
    def test_cannot_fall_back_to_old_setting(self):
        with self.assertRaises(ImproperlyConfigured):
            crypto.get_backend()

    def test_key_rotation(self):
        message = 'watch out for feral cats'
        key1 = Fernet.generate_key()

        with self.settings(ENCRYPTED_COOKIE_KEYS=[key1]):
            token = crypto.get_backend().encrypt(message)

        # Decrypt a value using an old key:
        with self.settings(ENCRYPTED_COOKIE_KEYS=[Fernet.generate_key(),
                                                  key1]):
            value = crypto.get_backend().decrypt(token)

        self.assertEqual(value, message)


@override_settings(ENCRYPTED_COOKIE_BACKEND='M2Crypto',
                   ENCRYPTED_COOKIE_KEYS=['some long string'])
class M2CryptoTests(BackendTests):

    def test_lookup(self):
        self.assertEqual(self.backend.module_name, 'M2Crypto')

    def test_fall_back_to_old_key_setting(self):
        with self.settings(ENCRYPTED_COOKIE_KEYS=None,
                           ENCRYPTED_COOKIE_KEY='this is an old key'):
            backend = crypto.get_backend()
        backend.decrypt(backend.encrypt('some message'))

    def test_fall_back_to_django_secret_key(self):
        with self.settings(ENCRYPTED_COOKIE_KEYS=None,
                           ENCRYPTED_COOKIE_KEY=None,
                           SECRET_KEY='this is django secret'):
            backend = crypto.get_backend()
        backend.decrypt(backend.encrypt('some message'))

    @override_settings(ENCRYPTED_COOKIE_KEYS=None,
                       ENCRYPTED_COOKIE_KEY=None,
                       SECRET_KEY='')
    def test_empty_key_not_allowed(self):
        with self.assertRaises(ImproperlyConfigured):
            crypto.get_backend().encrypt('summat')

    @override_settings(ENCRYPTED_COOKIE_KEYS=['key1', 'key2'])
    def test_key_rotation_not_supported(self):
        with self.assertRaises(NotImplementedError):
            crypto.get_backend().encrypt('summat')

    def test_encrypt_decrypt(self):
        message = 'the house key is under the mat'
        token = self.backend.encrypt(message)
        self.assertEqual(self.backend.decrypt(token), message)

    def test_reraise_decryption_errors(self):
        with self.settings(ENCRYPTED_COOKIE_KEYS=['first key']):
            token = crypto.get_backend().encrypt('message')
        with self.assertRaises(crypto.DecryptionError):
            with self.settings(ENCRYPTED_COOKIE_KEYS=['second key']):
                crypto.get_backend().decrypt(token)
