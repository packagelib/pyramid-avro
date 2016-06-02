import logging
import os
import shlex
import subprocess
import sys

from avro import protocol as avro_protocol

logger = logging.getLogger(__name__)


# TODO: Bring this under test.
def run_subprocess_command(command, out_stream=sys.stdout, bail=True):
    encoding = sys.stdout.encoding or "utf-8"
    if hasattr(command, "__iter__"):
        command = " ".join(command)

    command = shlex.split(command)
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    while proc.poll() is None:
        line = proc.stdout.readline()[:-1].strip()
        if line and out_stream:
            out_stream.write(line.decode(encoding))
            out_stream.write("\n")

    line = proc.stdout.read()[:-1].strip()

    if line and out_stream:
        out_stream.write(line.decode(encoding))
        out_stream.write("\n")

    exit_code = proc.returncode
    if bail and exit_code != 0:
        sys.exit(exit_code)

    return exit_code


def compile_protocol(protocol, schema, jar_file):

    if None in [protocol, schema, jar_file]:
        raise ValueError("Input must not be NoneType.")

    if not os.path.exists(jar_file):
        raise OSError("No such file or directory {}".format(jar_file))

    if not os.path.exists(protocol):
        raise OSError("No such file or directory {}".format(protocol))

    logger.debug("Compiling {} into {}".format(protocol, schema))
    command = [
        "java",
        "-jar",
        jar_file,
        "idl",
        protocol,
        schema
    ]
    run_subprocess_command(command)


def get_protocol_from_file(schema_path):

    if not isinstance(schema_path, basestring):
        raise ValueError("Schema path must be of type {}".format(basestring))

    if not os.path.exists(schema_path):
        raise OSError("No such file or directory '{}'".format(schema_path))

    with open(schema_path) as _file:
        protocol = avro_protocol.parse(_file.read())

    return protocol


__all__ = [compile_protocol.__name__]
