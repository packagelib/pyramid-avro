import io
import os
import unittest

import mock
import pytest
import webtest
from avro import ipc as avro_ipc
from avro import protocol as avro_protocol
from avro import schema as avro_schema
from webob import exc as http_exc

from pyramid_avro import routes as pa_routes

here = os.path.abspath(os.path.dirname(__file__))
protocol_dir = os.path.join(here, "protocols")
dummy_protocol_file = os.path.join(protocol_dir, "test.avpr")
with open(dummy_protocol_file) as _file:
    dummy_protocol = _file.read()
dummy_avro_protocol = avro_protocol.Parse(dummy_protocol)


class HTTPBogus(http_exc.HTTPOk):
    code = 1000


def raise_out(request):
    raise Exception("Raise out")


class CachedBufferTransceiver(object):
    req_resource = "/"
    status = None

    def __init__(self, webtest_app, resource):
        self.webtest_app = webtest_app
        self.resource = resource

    @property
    def remote_name(self):
        return self.__class__.__name__

    @classmethod
    def format_message(cls, message):
        with io.BytesIO() as _buffer:
            framed_writer = avro_ipc.FramedWriter(_buffer)
            if not hasattr(framed_writer, "_writer"):
                framed_writer._writer = framed_writer.writer
            framed_writer.Write(message)
            message = framed_writer._writer.getvalue()
        return message

    @classmethod
    def read_message(cls, response):
        with io.BytesIO() as _buffer:
            _buffer.write(response.body)
            _buffer.seek(os.SEEK_SET)
            framed_reader = avro_ipc.FramedReader(_buffer)
            response = framed_reader.Read()
        return response

    def transceive(self, request):
        message = self.format_message(request)
        self.cached_request_buffer = io.BytesIO()
        self.cached_request_buffer.write(message)

    def Transceive(self, request):
        return self.transceive(request)


class CachedBufferRequestor(avro_ipc.BaseRequestor):

    def issue_request(self, call_request, message_name, request_datum):
        self.transceiver.transceive(call_request)
        self.request_buffer = io.BytesIO(
            self.transceiver.cached_request_buffer.getvalue()
        )

    def _IssueRequest(self, *args, **kwargs):
        return self.issue_request(*args, **kwargs)


class RuntimeAppTransceiver(CachedBufferTransceiver):

    def transceive(self, request):
        message = self.format_message(request)
        response = self.webtest_app.post(
            self.resource,
            params=message,
            headers={"Content-Type": "avro/binary"},
            expect_errors=True
        )
        self.status = response.status_code
        return self.read_message(response)


class ServiceResponderTest(unittest.TestCase):

    def test_bad_executor(self):

        def bad_return_type(command, **args):
            return {}

        protocol = avro_protocol.Parse(dummy_protocol)
        _messages = getattr(
            protocol,
            "message_map",
            getattr(protocol, "messages")
        )
        get_msg = _messages.get("get")
        responder = pa_routes.ServiceResponder(bad_return_type, protocol)
        self.assertRaises(
            avro_ipc.AvroRemoteException,
            responder.Invoke,
            get_msg,
            {"arg1": "arg1"}
        )

    def test_good_executor(self):
        def good_return_type(command, **args):
            return "[{}] - arg1: {}".format(command, args["arg1"])

        protocol = avro_protocol.Parse(dummy_protocol)
        _messages = getattr(
            protocol,
            "message_map",
            getattr(protocol, "messages")
        )
        get_msg = _messages.get("get")
        responder = pa_routes.ServiceResponder(good_return_type, protocol)
        response = responder.Invoke(get_msg, {"arg1": "arg1"})
        self.assertEqual("[get] - arg1: arg1", response)


@pytest.mark.usefixtures("initialize_application")
class AvroServiceRouteTest(unittest.TestCase):

    def test_executor_message_undefined(self):
        route = pa_routes.AvroServiceRoute("/foo", dummy_protocol)
        self.assertRaises(
            avro_ipc.AvroRemoteException,
            route.execute_command,
            "not-defined"
        )

        self.assertRaises(
            avro_schema.AvroException,
            route.register_message_impl,
            "not-defined", raise_out
        )

    def test_executor_impl_exception(self):
        route = pa_routes.AvroServiceRoute("/foo", dummy_protocol)
        route.register_message_impl("get", raise_out)

        self.assertRaises(
            avro_ipc.AvroRemoteException,
            route.execute_command,
            "get"
        )

    def _route_and_request(self, invalid_request=False):
        environ = {
            "CONTENT_TYPE": "avro/binary",
            "CONTENT_LENGTH": 0,
            "REQUEST_METHOD": "POST"
        }

        if not invalid_request:
            requestor = CachedBufferRequestor(
                dummy_avro_protocol,
                CachedBufferTransceiver(self.app, "/foo")
            )
            requestor.Request("get", {"arg1": "arg"})

            body = requestor.request_buffer.getvalue()
            environ["wsgi.input"] = io.BytesIO(body)
            environ["CONTENT_LENGTH"] = len(body)

        route = pa_routes.AvroServiceRoute("/foo", dummy_protocol)
        request = webtest.TestRequest.blank("/foo", environ)
        return route, request

    def test_invalid_request(self):
        route, request = self._route_and_request(invalid_request=True)
        self.assertRaises(http_exc.HTTPBadRequest, route, request)

    def test_view_connection_closed(self):

        route, request = self._route_and_request()
        with mock.patch(
                "avro.ipc.FramedReader.Read",
                side_effect=avro_ipc.ConnectionClosedException()
        ):
            response = route(request)
            self.assertEqual(400, response.status_code)

    def test_view_http_exception(self):
        route, request, = self._route_and_request()
        with mock.patch(
            "pyramid_avro.routes.ServiceResponder.Respond",
            side_effect=HTTPBogus()
        ):
            response = route(request)
            self.assertEqual(1000, response.status_code)

    def test_view_generic_exception(self):
        route, request = self._route_and_request()
        with mock.patch(
            "pyramid_avro.routes.ServiceResponder.Respond",
            side_effect=Exception("Generic Exception")
        ):
            response = route(request)
            self.assertEqual(500, response.status_code)


@pytest.mark.usefixtures("initialize_application")
class AccessWithClientTest(unittest.TestCase):

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

    def _do_request(self, method, args):
        app_transceiver = RuntimeAppTransceiver(self.app, "/foo")
        protocol = avro_protocol.Parse(dummy_protocol)
        requestor = avro_ipc.Requestor(protocol, app_transceiver)
        response = requestor.Request(method, args)
        return app_transceiver.status, response

    def test_good_client_good_impl(self):
        # Check with good response.
        status, response = self._do_request("get", {"arg1": "arg1"})
        self.assertEqual(200, status)
        self.assertEqual("arg1", response)

    def test_good_client_bad_impl(self):
        self.assertRaises(
            avro_ipc.AvroRemoteException,
            self._do_request,
            "get2", {"arg1": "arg"}
        )
