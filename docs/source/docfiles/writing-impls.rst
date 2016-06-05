.. _writing-impls:

Writing Implementations
=======================

Message implementations can be done as free-standing functions or two different forms of object instance methods.

Pure Configuration
------------------

You can register a message implementation through pure config::

    from pyramid.config import Configurator


    def main(global_config, **settings):
        config = Configurator(settings=settings)

        config.include("pyramid_avro")

        # The message name can be derived from the function
        config.register_avro_route("hello", "avro_project.views:hello_world")

        # Or set explicitly
        config.register_avro_route("hello", "avro_project.views:other_message",
            message="other_message")

Using Decorators
----------------

Free-standing functions
^^^^^^^^^^^^^^^^^^^^^^^

Define a simple implementation function is as easy as follows::

    # The message name can be derived from the function
    @avro_message(service_name="hello")
    def hello_world(request):
        return "Hello, {}!".format(request.avro_data["arg"])

    # Or set explicitly
    @avro_message(service_name="hello", message="other_message")
    def other_message_impl(request):
        return "Hello, other {}!".format(request.avro_data["arg"])


It's possible to use an object instance for implementing your service methods, too.

There are two ways service routes can be defined.

Classes: Service Name Specified
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The service name can be setup under the class as a property::

    class HelloProtocol(object):

        service_name = "hello"

        # The message name can be derived from the function
        @avro_message()
        def hello_world(self, request):
            return "Hello, {}!".format(request.avro_data["arg"])

        # Or set explicitly
        @avro_message(message_name="other_message")
        def other_message_impl(self, request):
            return "Hello, other {}!".format(request.avro_data["arg"])


Classes: Service Name Derived
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Or the name can be derived from the class name (it's `.lower()`'d)::

    class Hello(object):

        # The message name can be derived from the function
        @avro_message()
        def hello_world(self, request):
            return "Hello, {}!".format(request.avro_data["arg"])

        # Or set explicitly
        @avro_message(message_name="other_message")
        def other_message_impl(self, request):
            return "Hello, other {}!".format(request.avro_data["arg"])
