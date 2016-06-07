import types
import unittest

from pyramid_avro import version


class VersionTest(unittest.TestCase):

    def test_version_obj(self):
        self.assertIsInstance(version.version_info, types.TupleType)
        self.assertEqual(3, len(version.version_info))

    def test_dunder(self):
        self.assertIsInstance(version.__version__, str)
        self.assertEqual("0.0.2", version.__version__)
