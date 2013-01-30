# -*- coding: utf-8 -*-
# (c) 2013 Bright Interactive Limited. All rights reserved.
# http://www.bright-interactive.com | info@bright-interactive.com
from django.test import TestCase
from django.test.utils import override_settings
from encrypted_cookies import crypto


class EncryptionTests(TestCase):
    @override_settings(SECRET_KEY='')
    def test_empty_secret_key_not_allowed(self):
        with self.assertRaises(ValueError):
            crypto.encrypt('summat')

    def test_encrypt_decrypt(self):
        bytes = 'adsfasdfw34wras'
        encrypted = crypto.encrypt(bytes)
        self.assertNotEqual(bytes, encrypted)
        decrypted = crypto.decrypt(encrypted)
        self.assertEqual(bytes, decrypted)

    def test_multiple_encrypt_decrypt(self):
        """
        Make sure that crypto isn't invalidly reusing a same cipher object
        in a feedback mode (such as MODE_CFB)
        """
        bytes = 'adsfasdfw34wras'
        encrypted = crypto.encrypt(bytes)
        crypto.encrypt('asdf')
        decrypted = crypto.decrypt(encrypted)
        self.assertEqual(bytes, decrypted)
