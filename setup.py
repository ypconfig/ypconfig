from setuptools import setup, find_packages
from ypconfig import __version__


setup(
    name="ypconfig",
    version=__version__,
    description="Configure your Linux network interfaces from YAML.",
    author="Mark Schouten",
    author_email="mark@tuxis.nl",
    url="https://github.com/ypconfig/ypconfig",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.11",
    ],
    license="BSD 2-Clause",
    install_requires=[
        "schema==0.7.5",
        "pyroute2==0.7.12",
        "PyYAML==6.0",
        "docopt==0.6.2",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    platforms=["linux"],
    data_files=[],
    entry_points={"console_scripts": ["ypconfig = ypconfig.cli:main"]},
)
