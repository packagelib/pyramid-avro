pyramid-avro
============

This project is a Pyramid plugin built for integrating Avro protocol files into a pyramid application.

Python 3 Support
----------------
Unfortunately it is not yet available, as this plugin depends on Apache's [avro](https://pypi.python.org/pypi/avro/) library.
Python3 support will come in later versions.

A Note On Compilation
---------------------

While this plugin provides for auto-compiling your avro protocol into an avro schema, this is rarely something you'd want in all environments your application might be deployed into.

When defining a service configuration, you **must have at least a schema defined**.
This means that the protocol file itself isn't actually ever required **UNLESS** the auto_compile flag is turned on.

For non-development configs, we suggest compiling your schema files prior to deployments and simply specifying them in your config rather turning auto_compile on.

Lastly, the tools jar must be provided by you, the developer, not this plugin.
In addition to not wanting a compilation at runtime in non-dev environments, you probably don't want that jar hanging around either.


Actual Docs
-----------
The official documentation can be found at: https://pyramid-avro.readthedocs.org/

* **PyPI**: https://pypi.python.org/pypi/pyramid-avro/
* **Coverage**: [![Coverage Status](https://coveralls.io/repos/github/packagelib/pyramid-avro/badge.svg?branch=master)](https://coveralls.io/github/packagelib/pyramid-avro?branch=master)
* **Build Status**: [![Build Status](https://travis-ci.org/packagelib/pyramid-avro.svg?branch=master)](https://travis-ci.org/packagelib/pyramid-avro)
* **License**: Apache License (2.0)
