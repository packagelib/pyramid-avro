import logging
import os
import shlex
import subprocess
import sys

from avro import protocol as avro_protocol

logger = logging.getLogger(__name__)


def run_subprocess_command(command, out_buffer=sys.stdout, exit_on_error=True):
    """
    Execute a subprocess based on the provided command.

    If an out_buffer is provided, we assume a buffer interface and write the
    contents of the subprocess's stdout to it.

    if exit_on_error is provided, we call sys.exit if the exit code of the
    executed subprocess was non-zero.

    This returns the exit code of the executed subprocess.

    :param command: a string or iterable with strings as a command to exec.
    :param out_buffer: an optional output buffer.
    :param exit_on_error: whether or not to kill this process on non-zero exit.
    :return: the exit code of the subprocess.
    """
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
        if line and out_buffer:
            try:
                out_buffer.write(line.decode(encoding))
            except TypeError:
                out_buffer.write(line)
            out_buffer.write("\n")

    line = proc.stdout.read()[:-1].strip()
    if line and out_buffer:
        try:
            out_buffer.write(line.decode(encoding))
        except TypeError:
            out_buffer.write(line)
        out_buffer.write("\n")

    exit_code = proc.returncode
    if exit_on_error and exit_code != 0:
        sys.exit(exit_code)

    return exit_code


def compile_protocol(protocol, schema, jar_file):
    """
    Given the provided protocol path, schema path, and jar file path, attempt
    to compile the protocol file into an avro schema.

    :param protocol: an avro protocol file path.
    :param schema: a file path to write the compiled schema.
    :param jar_file: a jar file to use for the compilation.
    """

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
    """
    Given the provided schema path, load the schema contents into memory and
    parse them into an avro.protocol.Protocol object.

    :param schema_path: a schema file path.
    :return: an avro.protocol.Protocol object.
    """

    if not isinstance(schema_path, basestring):
        raise ValueError("Schema path must be of type {}".format(basestring))

    if not os.path.exists(schema_path):
        raise OSError("No such file or directory '{}'".format(schema_path))

    with open(schema_path) as _file:
        protocol = avro_protocol.parse(_file.read())

    return protocol


__all__ = [compile_protocol.__name__]
