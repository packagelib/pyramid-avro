import json
import os
import tempfile
import unittest

import mock
from avro import protocol as avro_protocol

from pyramid_avro import utils as pa_utils

sub_proc_cmd = "pyramid_avro.utils.run_subprocess_command"


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

