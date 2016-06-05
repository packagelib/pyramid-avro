import unittest
import os

from pyramid import config as p_config

from pyramid_avro import decorators as pa_dec
from pyramid_avro import routes as pa_routes


here = os.path.abspath(os.path.dirname(__file__))
protocol_dir = os.path.join(here, "protocols")


class Foo(object):

    @pa_dec.avro_message()
    def get(self, request):
        pass

    @pa_dec.avro_message(message="get2")
    def get_other(self, request):
        pass


class Protocol(object):

    service_name = "bar"

    @pa_dec.avro_message()
    def get(self, request):
        pass

    @pa_dec.avro_message(message="get2")
    def get_other(self, request):
        pass


@pa_dec.avro_message(service_name="baz")
def get(request):
    pass


class AvroMessageDecorator(unittest.TestCase):

    def test_decorator_class(self):
        settings = {
            "avro.service.foo": "schema = protocols/test.avpr",
            "avro.service.bar": "schema = protocols/test.avpr",
            "avro.service.baz": "schema = protocols/test.avpr"
        }
        config = p_config.Configurator(settings=settings)
        config.include("pyramid_avro")
        config.scan()
        config.commit()

        # Test "foo"'s service route/registry.
        foo_utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.foo"
        )
        self.assertIsNotNone(foo_utility)
        self.assertEqual(foo_utility.dispatch["get"], Foo.get.im_func)
        self.assertEqual(foo_utility.dispatch["get2"], Foo.get_other.im_func)

        # Test "bar"'s service route/registry.
        bar_utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.bar"
        )
        self.assertIsNotNone(bar_utility)
        self.assertEqual(
            bar_utility.dispatch["get"],
            Protocol.get.im_func
        )
        self.assertEqual(
            bar_utility.dispatch["get2"],
            Protocol.get_other.im_func
        )

        # Test "baz"'s service route/registry.
        baz_utility = config.registry.queryUtility(
            pa_routes.IAvroServiceRoute,
            name="avro.baz"
        )
        self.assertEqual(baz_utility.dispatch["get"], get)

    def test_bad_fn_error(self):

        # Do a bad function without a service name
        global foo_method

        @pa_dec.avro_message()
        def foo(request):
            pass

        foo_method = foo

        settings = {
            "avro.service.foo": "schema = protocols/test.avpr",
            "avro.service.bar": "schema = protocols/test.avpr",
            "avro.service.baz": "schema = protocols/test.avpr"
        }
        config = p_config.Configurator(settings=settings)
        config.include("pyramid_avro")
        try:
            config.scan()
        except AttributeError:
            pass
        else:
            self.assertTrue(False, "AttributeError not raised.")

        foo_method = None
