"""
Options to enter into a config:

# Path prefix for route access.
avro.default_path_prefix = /avro-api

# Protocol file directory.
avro.protocol_dir = %(here)s/avro_project/protocols

# Run compilation of protocol -> schema on start-up.
avro.auto_compile = true

# Tools jar must be defined if compile is truthy.
avro.tools_jar = %(here)s/avro_project/lib/avro-tools-1.7.7.jar

# Define services.
avro.service.foo =
    protocol_file = foo.avdl
    pattern = /avro/foo

avro.service.baz =
    pattern = /avro/baz

avro.service.other =
    schema_file = baz.avpr
"""
import logging

from pyramid import config as p_config
from pyramid import settings as p_settings

logger = logging.getLogger(__name__)

CONFIG_PREFIX = "avro."

CONFIG_DEFAULTS = {
    "default_path_prefix": None,
    "protocol_dir": None,
    "auto_compile": False,
    "tools_jar": None,
    "service": {}
}

SERVICE_DEF_PROPERTIES = frozenset((
    "protocol_file",
    "schema_file",
    "pattern"
))


def get_config_options(configuration):
    options = CONFIG_DEFAULTS.copy()
    parsed_options = dict(
        (key[len(CONFIG_PREFIX):], val)
        for key, val in configuration.items()
        if key.startswith(CONFIG_PREFIX)
    )
    for key in parsed_options.keys():
        val = parsed_options[key]
        if key.startswith("service."):
            if not isinstance(val, basestring) or not val:
                raise p_config.ConfigurationError(
                    "Service definition must have one on {}".format(
                        list(SERVICE_DEF_PROPERTIES)
                    )
                )
            service_name = key.replace("service.", "")
            services = options.get("service") or {}
            service_def_parts = [el for el in val.split('\n') if el]
            service_def = {}
            for part in service_def_parts:
                opt, value = part.split("=")
                opt = opt.strip()
                if opt not in SERVICE_DEF_PROPERTIES:
                    raise p_config.ConfigurationError(
                        "Unrecognized service property: '{}'".format(opt)
                    )
                value = value.strip()
                service_def[opt] = value

            services[service_name] = service_def
            key = "service"
            val = services
        options[key] = val

    auto_compile = p_settings.asbool(options.get("auto_compile"))
    tools_jar = options.get("tools_jar") or None
    valid_tools_jar = isinstance(tools_jar, basestring) and tools_jar

    if auto_compile and not valid_tools_jar:
        err = "'tools_jar' must be defined if 'auto_compile' is turned on."
        raise p_config.ConfigurationError(err)
    options["auto_compile"] = auto_compile
    return options


def derive_service_path(service_name, url_pattern=None, path_prefix=None):

    if not isinstance(service_name, basestring) or not service_name:
        raise ValueError("Service name must be a non-empty string.")

    path_parts = []
    if not isinstance(url_pattern, basestring) or not url_pattern:
        url_pattern = service_name

    if url_pattern.startswith("/"):
        url_pattern = url_pattern[1:]

    if isinstance(path_prefix, basestring) and path_prefix:
        if not path_prefix.startswith("/"):
            path_prefix = "/" + path_prefix
        path_parts.append(path_prefix)

    path_parts.append(url_pattern)

    url_pattern = "/".join(path_parts)
    if not url_pattern.startswith("/"):
        url_pattern = "/" + url_pattern

    return url_pattern


__all__ = [get_config_options.__name__]
