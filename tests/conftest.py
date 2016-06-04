import os

import pytest
import webtest

from pyramid import config as p_config


here = os.path.abspath(os.path.dirname(__file__))
protocol_dir = os.path.join(here, "protocols")
schema_file = os.path.join(protocol_dir, "test.avpr")
test_db = os.path.abspath(
    os.path.join(
        here,
        os.pardir,
        ".dev-data",
        "db",
        "test.sqlite"
    )
)
if os.path.exists(test_db):
    os.remove(test_db)


def get_impl(request):
    return "{}".format(request.avro_data["arg1"])


def test_app(global_config, **app_settings):
    config = p_config.Configurator(settings=app_settings)
    config.include("pyramid_avro")
    config.add_avro_route("foo", schema=schema_file)
    config.register_avro_message("foo", get_impl, "get")
    return config.make_wsgi_app()


@pytest.fixture(scope="module")
def settings():
    settings_dict = {"pyramid_includes": ["pyramid_avro"]}
    return settings_dict


@pytest.fixture(scope="module")
def default_test_app(settings):
    app = webtest.TestApp(test_app({}, **settings))
    return app


@pytest.fixture(scope="class")
def initialize_application(request, default_test_app):
    request.cls.app = default_test_app
