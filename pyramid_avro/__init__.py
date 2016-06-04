import logging
import os
import traceback

from pyramid import config as p_config
from pyramid import exceptions as p_exc

from . import routes
from . import settings
from . import utils

logger = logging.getLogger(__name__)


def add_avro_route(config, service_name, pattern=None, protocol=None,
                   schema=None):

    avro_settings = settings.get_config_options(config.get_settings())
    service_def = avro_settings.get("service").get(service_name)
    no_service_def = protocol is None and schema is None
    if no_service_def and service_def is None:
        err = "Not enough information provided to register service '{}'. " \
              "Please provide an ini file definition or a " \
              "protocol/schema when calling 'add_avro_route'.".format(
                service_name)

        raise p_config.ConfigurationError(err)

    # Derive service url path.
    service_path = settings.derive_service_path(
        service_name,
        pattern,
        avro_settings["default_path_prefix"]
    )

    # Derive base directory for files.
    base_dir = avro_settings["protocol_dir"]
    if base_dir is None or not os.path.isabs(base_dir):
        parts = [os.path.dirname(config.root_package.__file__)]
        if base_dir is not None:
            parts.append(base_dir)
        base_dir = os.path.join(*parts)

    # Discover protocol and schema files.
    if protocol is not None:
        if not os.path.isabs(protocol):
            # Make sure this is an absolute path.
            protocol = os.path.join(base_dir, protocol)

        # If schema was none, "auto-discover" it.
        if schema is None:
            directory, filename = os.path.split(protocol)
            filename, ext = os.path.splitext(filename)
            filename = ".".join([filename, "avpr"])
            schema = os.path.join(directory, filename)

    # Normalize schema path.
    if schema is not None:
        if not os.path.isabs(schema):
            schema = os.path.join(base_dir, schema)

    auto_compile = avro_settings["auto_compile"]
    if not auto_compile and not os.path.exists(schema):
        raise p_config.ConfigurationError(
            "No such file or directory '{}'".format(schema)
        )

    if avro_settings["auto_compile"]:
        tools_jar = avro_settings["tools_jar"]
        if tools_jar is None:
            err = "Cannot auto_compile without tools_jar defined."
            raise p_config.ConfigurationError(err)

        if not os.path.exists(tools_jar):
            err = "No such file or directory: {}".format(tools_jar)
            raise p_config.ConfigurationError(err)

        if protocol is None:
            err = "Cannot auto_compile without a protocol defined."
            raise p_config.ConfigurationError(err)

    def register():
        # Begin route definition.
        route = ".".join(["avro", service_name])
        registry = config.registry
        # Shadow outer-scope
        protocol_file = protocol
        schema_file = schema

        if avro_settings["auto_compile"]:
            utils.compile_protocol(protocol_file, schema_file, tools_jar)

        try:
            with open(schema_file) as _file:
                schema_contents = _file.read()
        except Exception:
            message = traceback.format_exc()
            raise p_config.ConfigurationError(message)

        try:
            route_def = routes.AvroServiceRoute(route, schema_contents)
        except Exception:
            raise p_exc.ConfigurationError(
                "Failed to register route {}:\n {}".format(
                    service_name,
                    traceback.format_exc()
                )
            )

        registry.registerUtility(
            route_def,
            routes.IAvroServiceRoute,
            name=route
        )
        logger.debug("Registering avro service: {} => {}".format(
            route,
            service_path
        ))
        config.add_route(route, service_path, request_method="POST")
        config.add_view(route_name=route, view=route_def)

    config.action(
        ("avro-route", service_name),
        register,
        order=p_config.PHASE0_CONFIG
    )


def register_avro_message(config, service_name, message_impl, message=None):

    if isinstance(message_impl, str):
        message_impl = config.maybe_dotted(message_impl)

    if not callable(message_impl):
        raise p_exc.ConfigurationError(
            "{} must be callable.".format(message_impl)
        )

    message_name = message or message_impl.__name__
    route = ".".join(["avro", service_name])

    def register():
        registry = config.registry
        route_def = registry.queryUtility(routes.IAvroServiceRoute, name=route)
        if route_def is None:
            err = "Service '{}' has no route defined.".format(service_name)
            raise p_exc.ConfigurationError(err)

        logger.debug("Registering message {} for service {}".format(
            message_name,
            route
        ))
        route_def.register_message_impl(message_name, message_impl)

    config.action(
        ("avro-message", service_name, message_name),
        register,
        order=p_config.PHASE0_CONFIG
    )


def includeme(config):
    config.add_directive("add_avro_route", add_avro_route)
    config.add_directive("register_avro_message", register_avro_message)
    options = settings.get_config_options(config.get_settings())
    service_defs = options.get("service") or {}
    for service_name, service_opts in service_defs.items():
        config.add_avro_route(service_name, **service_opts)

    logger.debug("Finished preparing for avro services.")


__all__ = [includeme.__name__]
