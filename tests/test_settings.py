import unittest

from pyramid import config as p_config
from pyramid import settings as p_settings

from pyramid_avro import settings as pa_settings


TRUTHY = list(p_settings.truthy) + [True, 1]
BAD_INPUT = ["", None, False, True, 1, 0]


class DeriveServicePathTest(unittest.TestCase):

    def test_empty_name(self):
        # Test bad stuff blows up
        for val in BAD_INPUT:
            self.assertRaises(
                ValueError,
                pa_settings.derive_service_path,
                val
            )

    def test_path_pattern(self):
        service_name = "foo"
        path_prefix = None
        provided_pattern = None

        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/foo")

        # Try with an empty string.
        provided_pattern = ""
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/foo")

        # Try with a non-abs pattern, no prefix.
        provided_pattern = "bar/baz"

        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/bar/baz")

        # Try with abs pattern, no prefix.
        provided_pattern = "/bar/baz"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/bar/baz")

    def test_prefix(self):
        service_name = "foo"
        provided_pattern = None
        path_prefix = None

        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )

        self.assertEqual(url_pattern, "/foo")

        # Try with a prefix.
        path_prefix = "/prefix"

        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/foo")

        # Try with a non-absolute prefix
        path_prefix = "prefix"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/foo")

    def test_path_pattern_prefix(self):

        # Try with non-abs prefix + non-abs pattern
        service_name = "foo"
        path_prefix = "prefix"
        provided_pattern = "bar"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/bar")

        # Try with abs prefix + non-abs pattern
        path_prefix = "/prefix"
        provided_pattern = "bar"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/bar")

        # Try with non-abs prefix + abs pattern
        path_prefix = "prefix"
        provided_pattern = "/bar"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/bar")

        # try with abs prefix + abs pattern
        path_prefix = "/prefix"
        provided_pattern = "/bar"
        url_pattern = pa_settings.derive_service_path(
            service_name,
            provided_pattern,
            path_prefix
        )
        self.assertEqual(url_pattern, "/prefix/bar")


class GetConfigOptionsTest(unittest.TestCase):
    def test_empty(self):
        # Test an empty settings dict.
        defaults = {
            "default_path_prefix": None,
            "protocol_dir": None,
            "auto_compile": False,
            "tools_jar": None,
            "service": {}
        }
        settings = {}
        avro_settings = pa_settings.get_config_options(settings)

        self.assertEqual(defaults, avro_settings)

    def test_auto_compile_tools_input(self):

        settings = {"avro.auto_compile": True}
        self.assertRaises(
            p_config.ConfigurationError,
            pa_settings.get_config_options,
            settings
        )

        for val in BAD_INPUT:
            settings["tools_jar"] = val
            self.assertRaises(
                p_config.ConfigurationError,
                pa_settings.get_config_options,
                settings
            )

    def test_auto_compile_truthy(self):
        expected = {
            "default_path_prefix": None,
            "protocol_dir": None,
            "auto_compile": True,
            "tools_jar": "non-empty-string",
            "service": {}
        }
        settings = {"avro.tools_jar": "non-empty-string"}
        for val in TRUTHY:
            settings["avro.auto_compile"] = val
            actual = pa_settings.get_config_options(settings)
            self.assertDictEqual(expected, actual)

    def test_empty_service_def(self):
        foo_service_str = ""
        settings_dict = {"avro.service.foo": foo_service_str}
        self.assertRaises(
            p_config.ConfigurationError,
            pa_settings.get_config_options,
            settings_dict
        )

    def test_bad_service_prop(self):
        foo_service_str = "bogus = thing"
        settings_dict = {"avro.service.foo": foo_service_str}
        self.assertRaises(
            p_config.ConfigurationError,
            pa_settings.get_config_options,
            settings_dict
        )

    def test_service_def_properties(self):
        foo_service_str = "protocol_file = foo.avdl"
        settings_dict = {"avro.service.foo": foo_service_str}
        expected = {
            "default_path_prefix": None,
            "protocol_dir": None,
            "auto_compile": False,
            "tools_jar": None,
            "service": {
                "foo": {
                    "protocol_file": "foo.avdl"
                }
            }
        }
        actual = pa_settings.get_config_options(settings_dict)
        self.assertEqual(expected, actual)

        # Test adding pattern.
        foo_service_str += "\npattern = /foo"
        settings_dict["avro.service.foo"] = foo_service_str
        expected["service"]["foo"]["pattern"] = "/foo"
        actual = pa_settings.get_config_options(settings_dict)
        self.assertEqual(expected, actual)

        # Test adding schema path.
        foo_service_str += "\nschema_file = foo.avpr"
        settings_dict["avro.service.foo"] = foo_service_str
        expected["service"]["foo"]["schema_file"] = "foo.avpr"
        actual = pa_settings.get_config_options(settings_dict)
        self.assertEqual(expected, actual)

    def test_multiple_service_def(self):
        settings_dict = {
            "avro.service.foo": "protocol_file = foo.avdl",
            "avro.service.bar": "schema_file = bar.avpr",
        }
        expected = {
            "default_path_prefix": None,
            "protocol_dir": None,
            "auto_compile": False,
            "tools_jar": None,
            "service": {
                "foo": {
                    "protocol_file": "foo.avdl"
                },
                "bar": {
                    "schema_file": "bar.avpr"
                }
            }
        }
        actual = pa_settings.get_config_options(settings_dict)
        self.assertEqual(expected, actual)


class PyramidConfiguratorTest(unittest.TestCase):

    def test_includeme(self):
        app_settings = {}
        config = p_config.Configurator(settings=app_settings)
        config.include("pyramid_avro")
