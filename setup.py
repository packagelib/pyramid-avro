import os

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand


here = os.path.abspath(os.path.dirname(__file__))
test_dir = os.path.join(here, "tests")
__version__ = None


with open(os.path.join(here, "README.md")) as _file:
    README = _file.read().strip()
with open(os.path.join(here, "CHANGES.txt")) as _file:
    CHANGES = _file.read().strip()
with open(os.path.join(here, "requirements", "main.txt")) as _file:
    REQUIREMENTS = [l.strip() for l in _file.readlines()]
with open(os.path.join(here, "requirements", "test.txt")) as _file:
    TEST_REQUIREMENTS = REQUIREMENTS[:]
    TEST_REQUIREMENTS += [l.strip() for l in _file.readlines()]
with open(os.path.join(here, "pyramid_avro", "version.py")) as _file:
    exec(_file.read())


class PyTest(TestCommand):
    """Copied from py.test docs."""

    user_options = TestCommand.user_options + [
        ("with-coverage=", "c", "Generate coverage reports.")
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.with_coverage = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_suite = self.test_suite or test_dir
        self.test_args = [self.test_suite]
        self.test_args += ["-rw"]

        if self.with_coverage:
            self.test_args += [
                "--cov={}".format("pyramid_avro"),
                "--cov-report={}".format(self.with_coverage)
            ]

    def run_tests(self):
        import pytest
        pytest.main(self.test_args)


setup(
    name="pyramid-avro",
    version=__version__,
    description="Avro RPC Bindings for Pyramid",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    license="Apache License (2.0)",
    author="Alex Milstead",
    author_email="alex@amilstead.com",
    url="http://github.com/packagelib/pyramid-avro",
    keywords="pyramid avro",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    test_suite="tests",
    cmdclass={"test": PyTest}
)
