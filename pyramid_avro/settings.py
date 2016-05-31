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


def get_config_options(configuration):
    options = {}
    parsed_options = dict(
        (key[len(CONFIG_PREFIX):], val)
        for key, val in configuration.items()
        if key.startswith(CONFIG_PREFIX)
    )
    for key in parsed_options.keys():
        val = parsed_options[key]
        if key.startswith("service."):
            service_name = key.replace("service.", "")
            services = options.get("service") or {}
            service_def_parts = [el for el in val.split('\n') if el]
            service_def = {}
            for part in service_def_parts:
                opt, value = part.split('=')
                opt = opt.strip()
                value = value.strip()
                service_def[opt] = value
            services[service_name] = service_def
            key = "service"
            val = services
        options[key] = val

    tools_jar = options.get("tools_jar") or None
    auto_compile = p_settings.asbool(options.get("auto_compile"))
    if auto_compile and not tools_jar:
        err = "'tools_jar' must be defined if 'auto_compile' is turned on."
        raise p_config.ConfigurationError(err)
    options["auto_compile"] = auto_compile
    return options


__all__ = [get_config_options.__name__]
