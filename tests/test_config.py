import os
import unittest

import mock
from avro import schema as avro_schema
from pyramid import config as p_config

import pyramid_avro as pa
from pyramid_avro import routes as pa_routes


here = os.path.abspath(os.path.dirname(__file__))
protocol_dir = os.path.join(here, "protocols")
dummy_protocol_file = os.path.join(protocol_dir, "test.avdl")
dummy_schema_file = os.path.join(protocol_dir, "test.avpr")
dummy_tools_jar = os.path.join(protocol_dir, "tools.jar")

some_global = object()


def some_global_fn():
    pass


fqdn_val = ".".join([__name__, "some_global"])
fqdn_fn = ".".join([__name__, "some_global_fn"])


class PyramidConfigTest(unittest.TestCase):

    def test_empty_settings_include(self):
        # This won't blow up.
        settings = {}
        config = p_config.Configurator(settings=settings)
        config.include("pyramid_avro")

    def test_registered_directives(self):
        settings = {}
        config = p_config.Configurator(settings=settings)
        config.include("pyramid_avro")
        self.assertTrue(hasattr(config, "add_avro_route"))
        self.assertTrue(hasattr(config, "register_avro_message"))

    def test_predefined_service(self):
        settings = {
            "avro.service.foo": "protocol = protocols/test.avdl"
        }
        config = p_config.Configurator(settings=settings)
        config.include("pyramid_avro")
        config.commit()

        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )

        self.assertIsNotNone(utility)


class AddAvroRouteAutoCompileTest(unittest.TestCase):

    def test_bad_config(self):
        # Test config options with/out auto_compile.
        settings = {"avro.auto_compile": True}
        config = p_config.Configurator(settings=settings)
        try:
            pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        except p_config.ConfigurationError as ex:
            expected_error = "Cannot auto_compile without tools_jar defined."
            self.assertEqual(expected_error, ex.message)
        else:
            self.assertTrue(False, "Configuration exception not raised.")

        # Now test a bad tools jar location.
        settings["avro.tools_jar"] = "bogus-tools-jar"
        config = p_config.Configurator(settings=settings)
        try:
            pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        except p_config.ConfigurationError as ex:
            expected_error = "No such file or directory: bogus-tools-jar"
            self.assertEqual(expected_error, ex.message)
        else:
            self.assertTrue(False, "Configuration exception not raised.")

        # Now test with a tools_jar + schema but no protocol we boom.
        settings["avro.tools_jar"] = dummy_tools_jar
        config = p_config.Configurator(settings=settings)
        try:
            pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        except p_config.ConfigurationError as ex:
            expected_error = "Cannot auto_compile without a protocol defined."
            self.assertEqual(expected_error, ex.message)
        else:
            self.assertTrue(False, "Configuration exception not raised.")

    def test_derived_schema(self):
        # Actually test compilation.
        settings = {
            "avro.auto_compile": True,
            "avro.tools_jar": dummy_tools_jar
        }
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", protocol=dummy_protocol_file)

        compile_fn = "pyramid_avro.utils.compile_protocol"

        # The derived schema should be the same name/dir as protocol:
        directory, filename = os.path.split(dummy_protocol_file)
        filename, ext = os.path.splitext(filename)
        filename = ".".join([filename, "avpr"])
        expected_schema = os.path.join(directory, filename)
        with mock.patch(compile_fn) as _mocked_compile:
            config.commit()
            _mocked_compile.assert_called()
            _mocked_compile.assert_called_with(
                dummy_protocol_file,
                expected_schema,
                dummy_tools_jar
            )

    def test_explicit_schema(self):
        # Actually test compilation.
        settings = {
            "avro.auto_compile": True,
            "avro.tools_jar": dummy_tools_jar
        }
        config = p_config.Configurator(settings=settings)
        schema_file = os.path.join(protocol_dir, "test.my-file-ext")
        pa.add_avro_route(
            config,
            "foo",
            protocol=dummy_protocol_file,
            schema=schema_file
        )

        compile_fn = "pyramid_avro.utils.compile_protocol"
        with mock.patch(compile_fn) as _mocked_compile:
            with open(dummy_schema_file) as _file:
                with open(schema_file, "w") as _new_file:
                    _new_file.write(_file.read())
            config.commit()
            _mocked_compile.assert_called()
            _mocked_compile.assert_called_with(
                dummy_protocol_file,
                schema_file,
                dummy_tools_jar
            )


class AddAvroRouteTest(unittest.TestCase):

    def test_route_obj_exception(self):
        err = Exception("Weird error!")
        config = p_config.Configurator(settings={})
        config.include("pyramid_avro")
        config.add_avro_route("foo", schema="protocols/test.avpr")

        with mock.patch(
                "pyramid_avro.routes.AvroServiceRoute.__init__",
                side_effect=err
        ):
            self.assertRaises(
                p_config.ConfigurationError,
                config.commit
            )
            # Test the error was ours
            try:
                config.commit()
            except p_config.ConfigurationError as ex:
                message = ex.message
                self.assertIn(err.message, message)

    def test_bad_schema_file_read(self):
        err = Exception("Weird error!")
        config = p_config.Configurator(settings={})
        config.include("pyramid_avro")
        config.add_avro_route("foo", schema="protocols/test.avpr")

        with mock.patch("pyramid_avro.open", side_effect=err):
            # Test the error was ours
            try:
                config.commit()
            except p_config.ConfigurationExecutionError as ex:
                message = ex.evalue.message
                self.assertIn(err.message, message)
            else:
                self.assertTrue(False, "Configuration exception not raised.")

    def test_incomplete_settings(self):
        settings = {}
        self.assertRaises(
            p_config.ConfigurationError,
            pa.add_avro_route,
            p_config.Configurator(settings=settings),
            "foo"
        )

        self.assertRaises(
            p_config.ConfigurationError,
            pa.add_avro_route,
            p_config.Configurator(settings=settings),
            "foo",
            pattern="/foo"
        )

    def test_non_abs_protocol_dir(self):
        settings = {"avro.protocol_dir": "protocols"}
        # config.root_package will be this tests/__init__.py module.
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", schema="test.avpr")
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_abs_protocol_dir(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", schema="test.avpr")
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_non_abs_protocol_file(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", protocol="test.avdl")
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_abs_protocol_file(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", protocol=dummy_protocol_file)
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_non_abs_schema_file(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", schema="test.avpr")
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_abs_schema_file(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        config.commit()
        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(utility)

    def test_bad_schema_file(self):
        settings = {"avro.protocol_dir": protocol_dir}
        config = p_config.Configurator(settings=settings)
        self.assertRaises(
            p_config.ConfigurationError,
            pa.add_avro_route,
            config,
            "foo",
            schema="completely-bogus-schema-file"
        )

    def test_utility_result(self):
        # Test that the route util is registered.
        config = p_config.Configurator(settings={})
        pa.add_avro_route(
            config,
            "foo",
            schema=dummy_schema_file
        )
        config.commit()

        registry = config.registry
        utility = registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo",
        )
        self.assertIsNotNone(utility)


class RegisterAvroMessageTest(unittest.TestCase):

    def test_impl_format(self):
        # Test that the route util is registered.
        config = p_config.Configurator(settings={})

        self.assertRaises(
            ImportError,
            pa.register_avro_message,
            config,
            "foo",
            "some-bogus-value"
        )
        # Try global attr
        self.assertRaises(
            p_config.ConfigurationError,
            pa.register_avro_message,
            config,
            "foo",
            fqdn_val
        )

        # Try global fn.
        # SHOULD NOT BLOW UP
        pa.register_avro_message(config, "foo", fqdn_fn)

    def test_with_route(self):
        # Add a route:
        config = p_config.Configurator(settings={})
        pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        pa.register_avro_message(config, "foo", fqdn_fn)
        try:
            config.commit()
        except p_config.ConfigurationExecutionError as ex:
            expected_err = "Message 'some_global_fn' not defined."
            self.assertIsInstance(ex.evalue, avro_schema.AvroException)
            self.assertEqual(expected_err, ex.evalue.message)
        else:
            self.assertTrue(False, "AvroException not raised.")

        config = p_config.Configurator(settings={})
        pa.add_avro_route(config, "foo", schema=dummy_schema_file)
        pa.register_avro_message(config, "foo", fqdn_fn, message="get")

        config.commit()

        utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo",
        )
        self.assertIsNotNone(utility)
        self.assertIn("get", utility.dispatch)
        self.assertEqual(some_global_fn, utility.dispatch["get"])

    def test_empty_utility(self):
        # Try attr without route.
        config = p_config.Configurator(settings={})
        pa.register_avro_message(config, "foo", fqdn_fn)

        try:
            config.commit()
        except p_config.ConfigurationExecutionError as ex:
            expected_err = "Service 'foo' has no route defined."
            self.assertIn(expected_err, ex.evalue.message)
        else:
            self.assertTrue(False, "Configuration error not raised.")
