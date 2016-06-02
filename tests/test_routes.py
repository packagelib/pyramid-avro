import collections
import io
import os
import unittest

import pytest
from avro import ipc as avro_ipc
from avro import protocol as avro_protocol

from pyramid_avro import routes as pa_routes

here = os.path.abspath(os.path.dirname(__file__))
dummy_protocol_file = os.path.join(here, "test.json")
with open(dummy_protocol_file) as _file:
    dummy_protocol = _file.read()


class WriteBufferRequestor(avro_ipc.BaseRequestor):

    def __init__(self, response_buffer, *args, **kwargs):
        avro_ipc.BaseRequestor.__init__(self, *args, **kwargs)
        self.response_buffer = response_buffer

    def issue_request(self, call_request, message_name, request_datum):
        self.response_buffer.write(call_request)


class ServiceResponderTest(unittest.TestCase):

    def test_bad_executor(self):

        def bad_return_type(command, **args):
            return {}

        protocol = avro_protocol.parse(dummy_protocol)
        get_msg = protocol.messages.get("get")
        responder = pa_routes.ServiceResponder(bad_return_type, protocol)
        self.assertRaises(
            avro_ipc.AvroRemoteException,
            responder.invoke,
            get_msg,
            {"arg1": "arg1"}
        )

    def test_good_executor(self):
        def good_return_type(command, **args):
            return "[{}] - arg1: {}".format(command, args["arg1"])

        protocol = avro_protocol.parse(dummy_protocol)
        get_msg = protocol.messages.get("get")
        responder = pa_routes.ServiceResponder(good_return_type, protocol)
        response = responder.invoke(get_msg, {"arg1": "arg1"})
        self.assertEqual("[get] - arg1: arg1", response)


@pytest.mark.usefixtures("initialize_application")
class AvroServiceRouteTest(unittest.TestCase):

    def test_registration(self):
        response = self.app.get(
            "/foo",
            expect_errors=True
        )
        self.assertEqual(404, response.status_code)

        # Check bad request.
        response = self.app.post(
            "/foo",
            params="",
            expect_errors=True
        )
        self.assertEqual(400, response.status_code)

    def _get_request_body(self, method, args):
        f = collections.namedtuple("transceiver", "remote_name")
        with io.BytesIO() as _buffer:
            protocol = avro_protocol.parse(dummy_protocol)
            requestor = WriteBufferRequestor(
                _buffer,
                protocol,
                f("localhost")
            )
            requestor.request(method, args)
            contents = requestor.response_buffer.getvalue()
        return contents

    def _do_request(self, method, args):
        request_body = self._get_request_body(method, args)
        with io.BytesIO() as _write_buffer:
            writer = avro_ipc.FramedWriter(_write_buffer)
            writer.write_framed_message(request_body)
            content_length = len(_write_buffer.getvalue())
            _write_buffer.seek(os.SEEK_SET)
            headers = {
                "Content-Type": "avro/binary",
                "Content-Length": str(content_length)
            }
            response = self.app.request(
                "/foo",
                method="POST",
                headers=headers,
                body_file=_write_buffer
            )

        return response

    def _parse_response(self, response):
        with io.BytesIO(response.body) as response_buffer:
            response_buffer.seek(os.SEEK_SET)
            reader = avro_ipc.FramedReader(response_buffer)
            result = reader.read_framed_message()
            response_buffer.read()
        # SOme junk here because of endian-ness?
        result = result.lstrip('\x00').lstrip('\x08').lstrip('\x01').lstrip('\x00B')
        return result

    def test_good_client_good_impl(self):
        # Check with good response.
        response = self._do_request("get", {"arg1": "arg1"})
        self.assertEqual(200, response.status_code)

        result = self._parse_response(response)
        self.assertEqual("arg1", result)

    def test_good_client_bad_impl(self):
        response = self._do_request("get2", {"arg1": "arg1"})
        self.assertEqual(200, response.status_code)

        result = self._parse_response(response)
        self.assertEqual("No handler registered for: 'get2'", result)
