import logging
import os
import traceback

from pyramid import config as p_config
from pyramid import exceptions as p_exc

from . import routes
from . import settings
from . import utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def add_avro_route(config, service_name, pattern=None, protocol_file=None,
                   schema_file=None):

    def register():
        # Shadowing vars.
        avro_settings = settings.get_config_options(config.get_settings())
        registry = config.registry
        protocol_path = protocol_file
        schema_path = schema_file
        # Start route discovery.
        route = ".".join(["avro", service_name])

        base_dir = avro_settings["protocol_dir"]
        if base_dir is None or not os.path.isabs(base_dir):
            pkg_root = os.path.dirname(config.root_package.__file__)
            parts = [pkg_root]
            if base_dir is not None:
                parts.append(base_dir)
            base_dir = os.path.join(*parts)

        service_path = settings.derive_service_path(
            service_name,
            pattern,
            avro_settings.get("default_path_prefix")
        )
        # Discover protocol and schema files.
        if protocol_path is not None:
            if not os.path.isabs(protocol_path):
                # Make sure this is an absolute path.
                protocol_path = os.path.join(base_dir, protocol_path)

        # If schema wasn't given, try to auto-discover it.
        if schema_path is not None:
            if not os.path.isabs(schema_path):
                schema_path = os.path.join(base_dir, schema_path)

            if protocol_path is None:
                directory, filename = os.path.split(schema_path)
                filename, ext = os.path.splitext(filename)
                filename = ".".join([filename, "avdl"])
                protocol_path = os.path.join(directory, filename)

        if protocol_path is None:
            # Try to auto-discover the protocol file.
            filename = ".".join([service_name, "avdl"])
            protocol_path = os.path.join(base_dir, filename)

            # If we had no protocol path AND no schema, blow up.
            if schema_path is None and not os.path.exists(protocol_path):
                err = "Must have 'schema_file' or 'protocol_file' defined " \
                      "for service {}.".format(service_name)
                raise p_config.ConfigurationError(err)

        if schema_path is None:
            directory, filename = os.path.split(protocol_path)
            filename, ext = os.path.splitext(filename)
            filename = ".".join([filename, "avpr"])
            schema_path = os.path.join(directory, filename)

        if avro_settings["auto_compile"]:
            tools_jar = avro_settings["tools_jar"]
            if protocol_path is None or schema_path is None:
                err = "Must have 'schema_file' or 'protocol_file' defined " \
                      "for service {}.".format(service_name)
                raise p_config.ConfigurationError(err)

            utils.compile_protocol(protocol_path, schema_path, tools_jar)

        try:
            with open(schema_path) as _file:
                schema_contents = _file.read()
            route_def = routes.AvroServiceRoute(route, schema_contents)
        except Exception:
            err = "Failed to register route {}:\n {}".format(
                service_name,
                traceback.format_exc()
            )
            raise p_exc.ConfigurationError(err)

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


def set_avro_message(config, service_name, message_impl, message=None):

    if isinstance(message_impl, str):
        message_impl = config.maybe_dotted(message_impl)

    if not callable(message_impl):
        raise p_exc.ConfigurationError(
            "{} must be callable.".format(message_impl)
        )

    message_name = message or message_impl.__name__

    def register():
        registry = config.registry
        route = ".".join(["avro", service_name])
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
    config.add_directive("set_avro_message", set_avro_message)
    options = settings.get_config_options(config.get_settings())
    service_defs = options.get("service") or {}
    for service_name, service_opts in service_defs.items():
        config.add_avro_route(service_name, **service_opts)

    logger.debug("Finished preparing for avro services.")


__all__ = [includeme.__name__]
