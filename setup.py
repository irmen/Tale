"""
Setup script for distutils

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import tale
try:
    # try setuptools first, to get access to build_sphinx and test commands
    from setuptools import setup
    using_setuptools = True
except ImportError:
    from distutils.core import setup
    using_setuptools=False

print("version="+tale.__version__)

setup_args = dict(
    name='tale',
    version=tale.__version__,
    packages=['tale', 'tale.cmds', 'tale.items', 'tale.io', 'tale.demo', 'tale.demo.zones'],
    package_data={
        'tale': ['soul_adverbs.txt']
        },
    url='http://packages.python.org/tale',
    license='GPL v3',
    author='Irmen de Jong',
    author_email='irmen@razorvine.net',
    description='Mud, mudlib & interactive fiction framework',
    long_description="""Tale is a framework for creating mudlibs, muds and/or interactive fiction (text adventures).

It's still being developed and new features are implement along the way,
but the current version is quite capable of running an interactive fiction story world.

I'm focusing on the single player Interactive Fiction mode for the time being.
The multi-user aspects of the framework have been put on the back burner for now.

An example test/demo story is included in the ``stories`` directory of the distribution archive.
""",
    keywords="mud, mudlib, interactive fiction, text adventure",
    scripts=["scripts/tale-driver.cmd", "scripts/tale-driver"],
    platforms="any",
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)"
    ],
    install_requires=["blinker>=1.1", "appdirs"],
    requires=["blinker", "appdirs"]
)

if using_setuptools:
    setup_args["test_suite"]="nose.collector"    # use Nose to run unittests

setup(**setup_args)
