.. _avro-tools: http://www.apache.org/dyn/closer.cgi/avro/
.. _quickstart:

Quickstart
==========

Below are the minimal steps needed to get up and running with an avro-based pyramid app.

Setup Pyramid
-------------

Setup a virtualenv::

    virtualenv avro-project
    source avro-project/bin/activate

Install pyramid::

    pip install pyramid pyramid-avro

Create starter scaffold::

    pcreate avro-project

Then make sure your app is setup::

    cd avro-project && python setup.py develop

Avro
----

Download the avro-tools jar here: `avro-tools`_, and put it in a `lib` directory.

Make a `protocols` directory and add a simple "Hello, World!" avro protocol, called `hello.avdl`::

    protocol HelloProtocol {
        error Exception {
            string message;
        }

        string hello_world(string arg) throws Exception;
    }

Your file tree should now look like this::

        avro-project
        ├── avro_project
        │   ├── __init__.py
        │   ├── protocols
        │   │   └── hello.avdl
        │   ├── static
        │   │   ├── pyramid-16x16.png
        │   │   ├── pyramid.png
        │   │   └── theme.css
        │   ├── templates
        │   │   └── mytemplate.pt
        │   ├── tests.py
        │   └── views.py
        ├── CHANGES.txt
        ├── development.ini
        ├── lib
        │   └── avro-tools.jar
        ├── MANIFEST.in
        ├── production.ini
        ├── pytest.ini
        ├── README.txt
        └── setup.py


Configure Routes
----------------

In your development.ini file, add these options::

    pyramid_includes =
        pyramid_avro

    # Set the base URL path prefix, other wise it's /<service-name>
    avro.default_path_prefix = /avro

    # Set up base protocol dir.
    avro.protocol_dir = %(here)s/avro_project/protocols

    # Set auto-compile to true.
    avro.auto_compile = true

    # Where tools jar lives:
    avro.tools_jar = $(here)s/lib/avro-tools.jar

    # Begin service definitions:
    avro.service.hello =
        protocol = hello.avdl

Now we need to add an implementation for the `hello` message.
In the `views.py` file, add this::

    from pyramid_avro.decorators import avro_message


    @avro_message(service_name="hello", message="hello_world")
    def hello_handler(request):
        return "Hello, {}!".format(request.avro_data["arg"])

Now run the server in one terminal::

    pserve development.ini


Congratulations! You now have an avro service running on the `/avro/hello` endpoint of your pyramid application!

Client Integration
------------------

A simple `test_client.py` would look like the following::

    import os

    from avro import ipc
    from avro import protocol


    here = os.path.abspath(os.path.dirname(__file__))
    protocol_file = os.path.join(here, "avro_project", "protocols", "hello.avpr")


    if __name__ == "__main__":
        with open(protocol_file) as _file:
            protocol_object = protocol.parse(_file.read())
        driver = ipc.HTTPTransceiver("localhost", 6543, "/avro/hello")
        client = ipc.Requestor(protocol_object, driver)

        response = client.request("hello_world", {"arg": "World"})
        print response

And upon execution, you'd see::

    $ python test_client.py
    Hello, World!

