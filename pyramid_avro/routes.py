import copy
import io
import logging
import traceback

from avro import io as avro_io
from avro import ipc as avro_ipc
from avro import protocol as avro_protocol
from avro import schema as avro_schema
from pyramid import response as p_response
from pyramid import threadlocal as p_threadlocal
from webob import exc as http_exc
from zope import interface as zi

logger = logging.getLogger(__name__)


class ServiceResponder(avro_ipc.Responder):
    """
    An Avro service responder which executes a callback to get a response.
    """

    def __init__(self, executor, *args, **kwargs):
        """
        Overridden init to add an executor callback.

        :param executor: a callback to use for retrieving a response.
        :param args: regular avro.ipc.Responder args.
        :param kwargs: regular avro.ipc.Responder kwargs.
        """
        self.executor = executor
        super(ServiceResponder, self).__init__(*args, **kwargs)

    def invoke(self, msg, req):
        """
        Call self.executor, then verify that the response fits the protocol
        that this knows how to speak.

        :param msg: an avro message.
        :param req: request arguments.
        :return: an avro response.
        """
        response = self.executor(msg.name, **req)
        local_message = self.local_protocol.messages.get(msg.name)
        local_response = local_message.response
        is_valid = avro_io.validate(local_response, response)
        if not is_valid:
            err = "Server response did not conform to its local schema."
            logging.error(
                "{}; Response: {}, Schema: {}".format(
                    err, response, local_response
                )
            )
            raise avro_ipc.AvroRemoteException(err)
        return response


class IAvroServiceRoute(zi.Interface):

    protocol = zi.Attribute("""Avro protocol object.""")
    responder = zi.Attribute("""Avro service responder.""")


@zi.implementer(IAvroServiceRoute)
class AvroServiceRoute(object):

    protocol = None
    responder = None

    def __init__(self, path, schema):
        self.path = path
        self.dispatch = {}
        self.protocol = avro_protocol.parse(schema)
        self.responder = ServiceResponder(self.execute_command, self.protocol)

    def register_message_impl(self, message, message_impl):
        if self.protocol.messages.get(message) is None:
            raise avro_schema.AvroException(
                "Message '{}' not defined.".format(message)
            )

        self.dispatch[message] = message_impl

    def validate_request(self, request):
        """
        Place for validating an incoming request.

        Right now, it simply verifies that there is a non-zero content-length.

        Any additional validation required will be added here in the future.

        :param request: a webob request.
        """
        content_length = int(request.headers["content-length"])
        if request.body_file is None or content_length == 0:
            raise http_exc.HTTPBadRequest()

    def __call__(self, request):
        """
        Reads the avro request data, then call our responder to respond.

        This will end up executing "execute_command" below.

        After getting a response from the responder, form a pyramid response
        and return it.

        This is basically the view object registered as a pyramid route.

        TODO: Figure out a way to send the request object through to the
        handler such that an implementation can modify any attributes of that
        request that it needs.

        :param request: a pyramid request.
        :return: a pyramid response.
        """
        self.validate_request(request)
        reader = avro_ipc.FramedReader(request.body_file)
        try:
            request_data = reader.read_framed_message()
        except avro_ipc.ConnectionClosedException:
            logger.exception("Failed to process request.")
            return http_exc.HTTPBadRequest()

        try:
            rpc_response = self.responder.respond(request_data)
        except http_exc.HTTPException as ex:
            logger.exception("HTTP exception while processing message.")
            return ex
        except Exception:
            logger.exception("Error processing RPC content.")
            return http_exc.HTTPInternalServerError()

        with io.BytesIO() as _body_file:
            writer = avro_ipc.FramedWriter(_body_file)
            writer.write_framed_message(rpc_response)
            response_body = _body_file.getvalue()

        logger.debug("Finished request. Returning response.")
        return p_response.Response(
            status=200,
            body=response_body,
            headerlist=[("Content-Type", "avro/binary")]
        )

    def execute_command(self, command, **command_args):
        """
        Given the provided command and its arguments, retrieve a registered
        message callback and execute it.

        Prior to executing the registered callback, attach the provided
        arguments as an "avro_data" attribute on the request object.

        :param command: an avro message name.
        :param command_args: avro message arguments.
        :return: a response from the handler.
        """
        exists = command in self.protocol.props["messages"].keys()
        if not exists:
            err = "Message not found: '{}'".format(command)
            raise avro_ipc.AvroRemoteException(err)

        handler = self.dispatch.get(command)
        if handler is None:
            err = "No handler registered for: '{}'".format(command)
            raise avro_ipc.AvroRemoteException(err)

        try:
            logger.debug("Invoking handler {}".format(handler))
            request = p_threadlocal.get_current_request()
            request.avro_data = copy.deepcopy(command_args)
            response = handler(request)
        except Exception:
            logging.exception("Error handling request: {}".format(command))
            raise avro_ipc.AvroRemoteException(traceback.format_exc())

        return response


__all__ = [IAvroServiceRoute.__name__, AvroServiceRoute.__name__]
