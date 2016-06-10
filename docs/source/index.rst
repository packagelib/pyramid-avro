.. _avro-tools: http://www.apache.org/dyn/closer.cgi/avro/
.. Pyramid Avro documentation master file, created by
   sphinx-quickstart on Sat Jun  4 17:33:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyramid-avro's documentation!
========================================

This project is a Pyramid plugin built for integrating Avro protocol files into a pyramid application.

Be sure to check out the :ref:`Quickstart Project <quickstart>` documentation to get started.

:PyPi: https://pypi.python.org/pypi/pyramid-avro/
:Coverage:
   .. image:: https://coveralls.io/repos/github/packagelib/pyramid-avro/badge.svg?branch=master
        :target: https://coveralls.io/github/packagelib/pyramid-avro?branch=master
        :alt: Coverage Status
:Build Status:
   .. image:: https://travis-ci.org/packagelib/pyramid-avro.svg?branch=master
        :target: https://travis-ci.org/packagelib/pyramid-avro
        :alt: Build Status
:License: Apache License (2.0)

Python Version Support
----------------------
Current Supported Versions:

* 2.7
* 3.3
* 3.4
* 3.5

A Note On Compilation
---------------------

While this plugin provides for auto-compiling your avro protocol into an avro schema, this is rarely something you'd want in all environments your application might be deployed into.

When defining a service configuration, you **must have at least a schema defined**.
This means that the protocol file itself isn't actually ever required **UNLESS** the auto_compile flag is turned on.

For non-development configs, we suggest compiling your schema files prior to deployments and simply specifying them in your config rather turning auto_compile on.

Lastly, the tools jar must be provided by you, the developer, not this plugin.
In addition to not wanting a compilation at runtime in non-dev environments, you probably don't want that jar hanging around either.


Contents:

.. _main-toc
.. toctree::
   :maxdepth: 2

   docfiles/quickstart
   docfiles/config-options
   docfiles/writing-impls

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

