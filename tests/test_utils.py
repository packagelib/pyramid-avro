import json
import os
import io
import tempfile
import unittest
import sys

import mock
from avro import protocol as avro_protocol

from pyramid_avro import utils as pa_utils

sub_proc_cmd = "pyramid_avro.utils.run_subprocess_command"


class RunSubprocessCommandTest(unittest.TestCase):

    def test_function(self):
        _stdout_buffer = io.BytesIO()
        _stdout_buffer.seek(os.SEEK_SET)

        def _dummy_poll():
            if not _stdout_buffer.getvalue():
                _stdout_buffer.seek(os.SEEK_SET)
                _stdout_buffer.write(b"foo\n")
                _stdout_buffer.write(b"foo\n")
                _stdout_buffer.seek(os.SEEK_SET)
                return None
            return 0

        _capture_buffer = io.BytesIO()

        with mock.patch("pyramid_avro.utils.subprocess") as subprocess:
            subprocess.Popen.return_value.poll = _dummy_poll
            subprocess.Popen.return_value.stdout = _stdout_buffer
            subprocess.Popen.return_value.returncode = 0

            pa_utils.run_subprocess_command(
                ["echo", "'foo'"],
                out_buffer=_capture_buffer
            )
            output = _capture_buffer.getvalue()
            if not isinstance(output, str):
                output = output.decode("utf-8")
            self.assertEqual("foo\nfoo\n", output)

        with mock.patch("pyramid_avro.utils.subprocess") as subprocess:
            subprocess.Popen.return_value.poll = _dummy_poll
            subprocess.Popen.return_value.stdout = _stdout_buffer
            subprocess.Popen.return_value.returncode = 1

            self.assertRaises(
                SystemExit,
                pa_utils.run_subprocess_command,
                ["echo", "'foo'"]
            )


class CompileProtocolTest(unittest.TestCase):

    def test_bad_input(self):
        _, tmp_jar_file = tempfile.mkstemp("foo.jar")
        _, tmp_protocol = tempfile.mkstemp("foo.avdl")
        with mock.patch(sub_proc_cmd):
            protocol, schema, jar_file = None, None, None
            self.assertRaises(
                ValueError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )
            # Test with non-Nones.
            protocol = ""
            self.assertRaises(
                ValueError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )

            schema = ""
            self.assertRaises(
                ValueError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )

            # Test bad paths raise now.
            jar_file = ""
            self.assertRaises(
                OSError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )

            # Make jar file OK
            jar_file = tmp_jar_file
            self.assertRaises(
                OSError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )

            jar_file = ""
            protocol = tmp_protocol
            self.assertRaises(
                OSError,
                pa_utils.compile_protocol,
                protocol, schema, jar_file
            )

        # Clean up
        os.remove(tmp_jar_file)
        os.remove(tmp_protocol)

    def test_good_input(self):
        _, jar_file = tempfile.mkstemp("foo.jar")
        _, protocol = tempfile.mkstemp("bar.avdl")
        schema = ""
        expected_command = [
            "java", "-jar", jar_file, "idl", protocol, schema
        ]
        with mock.patch(sub_proc_cmd) as _mock_fn:
            pa_utils.compile_protocol(protocol, schema, jar_file)
            _mock_fn.assert_called_with(expected_command)

        os.remove(jar_file)
        os.remove(protocol)


class GetProtocolFromFileTest(unittest.TestCase):

    def test_bad_input(self):
        schema_path = None
        self.assertRaises(
            ValueError,
            pa_utils.get_protocol_from_file,
            schema_path
        )

        schema_path = "bad path"
        self.assertRaises(
            OSError,
            pa_utils.get_protocol_from_file,
            schema_path
        )

        _, schema_path = tempfile.mkstemp("foo.avpr")
        self.assertRaises(
            avro_protocol.ProtocolParseException,
            pa_utils.get_protocol_from_file,
            schema_path
        )

        protocol_dict = {
            "protocol": "Foo",
            "namespace": None,
            "types": [],
            "messages": {}
        }

        with open(schema_path, "w") as _file:
            json.dump(protocol_dict, _file)

        protocol = pa_utils.get_protocol_from_file(schema_path)
        self.assertIsNotNone(protocol)
        self.assertIsInstance(protocol, avro_protocol.Protocol)
        os.remove(schema_path)
