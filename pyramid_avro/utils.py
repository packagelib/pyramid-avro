import errno
import logging
import os
import shlex
import subprocess
import sys
import tempfile

import requests
from avro import protocol as avro_protocol

JAR_NAME = "avro-tools-1.7.7.jar"
AVRO_JAR_LINK = "http://apache.claz.org/avro/avro-1.7.7/java/{}".format(JAR_NAME)

DL_CHUNK_SIZE = 1024
DL_PATH = os.path.abspath(
    os.path.join(
        tempfile.gettempdir(),
        "pyramid-avro.download",
        JAR_NAME
    )
)


logger = logging.getLogger(__name__)


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


def download_jar():
    if not os.path.exists(DL_PATH) or not os.path.isfile(DL_PATH):
        dir_path = os.path.dirname(DL_PATH)
        try:
            os.makedirs(dir_path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
                pass
            else:
                raise

        response = requests.get(AVRO_JAR_LINK, stream=True)
        with open(DL_PATH, "wb") as _file:
            for chunk in response.iter_content(chunk_size=DL_CHUNK_SIZE):
                if chunk:
                    _file.write(chunk)
    return DL_PATH


def compile_protocol(protocol, schema, jar_file=None):
    jar_file = jar_file or download_jar()

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

    if not os.path.exists(schema_path):
        raise OSError("No such file or directory '{}'".format(schema_path))

    with open(schema_path) as _file:
        protocol = avro_protocol.parse(_file.read())

    return protocol


__all__ = [compile_protocol.__name__]
