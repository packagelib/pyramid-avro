import sys
import unittest

from avro import io as avro_io
from avro import ipc as avro_ipc
from avro import protocol as avro_protocol


def _patch_avro():
    avro_io.validate = avro_io.Validate
    avro_ipc.FramedReader.read_framed_message = avro_ipc.FramedReader.Read
    avro_ipc.FramedWriter.write_framed_message = avro_ipc.FramedWriter.Write
    avro_ipc.Responder.respond = avro_ipc.Responder.Respond
    avro_ipc.BaseRequestor.request = avro_ipc.BaseRequestor.Request
    avro_protocol.parse = avro_protocol.Parse
    avro_protocol.Protocol.messages = avro_protocol.Protocol.message_map


class Py2CompatTest(unittest.TestCase):

    def test_patch(self):
        py3 = sys.version_info[0] == 3
        if py3:
            _patch_avro()

        from pyramid_avro import py2_compat
        old_info = sys.version_info
        sys.version_info = [3]
        py2_compat.patch()
        self.assertIn("basestring", __builtins__)

        sys.version_info = [2]
        py2_compat.patch()
        self.assertIsNotNone(getattr(avro_io, "Validate", None))
        self.assertIsNotNone(getattr(avro_ipc.FramedReader, "Read", None))
        self.assertIsNotNone(getattr(avro_ipc.FramedWriter, "Write", None))
        self.assertIsNotNone(getattr(avro_ipc.Responder, "Respond", None))
        self.assertIsNotNone(getattr(avro_ipc.BaseRequestor, "Request", None))
        self.assertIsNotNone(getattr(avro_protocol, "Parse", None))
        self.assertIsNotNone(
            getattr(avro_protocol.Protocol, "message_map", None)
        )
        sys.version_info = old_info
        if not py3:
            __builtins__["basestring"] = (str, unicode)
