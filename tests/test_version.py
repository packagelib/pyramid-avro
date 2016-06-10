import types
import unittest

from pyramid_avro import version


class VersionTest(unittest.TestCase):

    def test_version_obj(self):
        self.assertIsInstance(version.version_info, tuple)
        self.assertEqual(3, len(version.version_info))

    def test_dunder(self):
        self.assertIsInstance(version.__version__, str)
        self.assertEqual("0.1.0", version.__version__)
