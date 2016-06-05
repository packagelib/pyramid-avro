.. _avro-tools: http://www.apache.org/dyn/closer.cgi/avro/
.. _config-options:

Configuring pyramid-avro
========================

Core configuration options:

* default_path_prefix: A default URL path prefix.
* protocol_dir: A path to a base directory for protocol files.
* auto_compile: Whether or not to automatically compile protocol -> schema on config commit.
* tools_jar: A path to an `avro-tools`_ (look for `avro-tools-X.Y.Z.jar`).
* service objects

    * schema: A path to a schema file.
    * protocol: A path to a protocol file.
    * pattern: A URL pattern.

Configuration Files
-------------------

Protocols can be configured inside pyramid config files as follows::

    # Make sure it's included:
    pyramid_includes =
        pyramid_avro

    # Run compilation of protocol -> schema on start-up.
    avro.auto_compile = false

    # All avro routes will be prepended by "/avro"
    avro.default_path_prefix = /avro

    # A base protocol directory.
    avro.protocol_dir = %(here)s/protocols

    # A tools jar reference.
    avro.tools_jar = %(here)s/avro_project/lib/avro-tools-1.7.7.jar

    # Service definitions.
    avro.service.foo =
        pattern = /avro/{val}/foo
        protocol = foo.avdl

    avro.service.bar =
        schema = bar.avpr
        pattern = /avro/other-bar

    avro.service.baz =
        schema = baz.avpr


Config Object/Programmatic
--------------------------

Protocols and message implementations can also be configured directly by calling pyramid-avro's config directives::

    from pyramid.config import Configurator


    def main(global_config, **settings):

        config = Configurator(settings=settings)
        config.include("pyramid_avro")

        config.add_avro_route("foo", pattern="/avro/{val}/foo",
            protocol="foo.avdl")
        config.add_avro_route("bar", pattern="/avro/other-bar",
            schema="bar.avpr")
        config.add_avro_route("baz", schema="baz.avpr")

        config.register_avro_message("foo", "my_project.views:impl", message="my_message")
        config.scan()
        return config.make_wsgi_app()

