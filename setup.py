from setuptools import setup, find_packages
from ypconfig import __version__

reqs = ["schema", "pyroute2", "PyYAML", "docopt"]

setup(
    name="ypconfig",
    version=__version__,
    description="Tools required for ypconfig",
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
    setup_requires=reqs,
    install_requires=reqs,
    packages=find_packages(exclude=["tests", "tests.*"]),
    platforms=["linux"],
    data_files=[],
    entry_points={"console_scripts": ["ypconfig = ypconfig.cli:main"]},
)
