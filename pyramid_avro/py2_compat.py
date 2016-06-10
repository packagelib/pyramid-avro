import sys

from avro import io as avro_io
from avro import ipc as avro_ipc
from avro import protocol as avro_protocol


def patch():
    if sys.version_info[0] == 3:
        __builtins__["basestring"] = (str,)
        return

    # Back-fill python3 calls.
    avro_io.Validate = avro_io.validate
    avro_ipc.FramedReader.Read = avro_ipc.FramedReader.read_framed_message
    avro_ipc.FramedWriter.Write = avro_ipc.FramedWriter.write_framed_message
    avro_ipc.Responder.Respond = avro_ipc.Responder.respond
    avro_ipc.BaseRequestor.Request = avro_ipc.BaseRequestor.request
    avro_protocol.Parse = avro_protocol.parse
    avro_protocol.Protocol.message_map = avro_protocol.Protocol.messages


patch()
