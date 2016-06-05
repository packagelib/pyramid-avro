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
    "protocol",
    "schema",
    "pattern"
))


def get_config_options(configuration):
    """
    Given a dictionary of config options, normalize and produce a resultant
    config dict for any keys prepended with "avro."

    The expectation here is that the configuration dict came straight from
    the result of parsing a config (.ini) file.

    :param configuration: a config dict.
    :return: a dict of config values for this plugin.
    """
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
            defined_protocol = "protocol" in service_def
            defined_schema = "schema" in service_def
            if not (defined_protocol or defined_schema):
                raise p_config.ConfigurationError(
                    "Service must have either protocol or schema defined."
                )

            services[service_name] = service_def
            key = "service"
            val = services
        options[key] = val
    options["auto_compile"] = p_settings.asbool(options.get("auto_compile"))
    return options


def derive_service_path(service_name, url_pattern=None, path_prefix=None):
    """
    Given a service name, existing url_pattern, and url path prefix, derive a
    normalized/finalized url path based on them.

    :param service_name: an avro service name.
    :param url_pattern: an optional existing url pattern.
    :param path_prefix: an optional path prefix.
    :return: a normalized url path.
    """

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
