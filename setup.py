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
    using_setuptools = False

print("version=" + tale.__version__)

setup_args = dict(
    name='tale',
    version=tale.__version__,
    packages=['tale', 'tale.cmds', 'tale.items', 'tale.tio', 'tale.demo', 'tale.demo.zones', 'tale.web'],
    package_data={
        'tale': ['soul_adverbs.txt'],
        'tale.tio': ['quill_pen_paper.ico', 'quill_pen_paper.gif'],
        'tale.web': ['*']
    },
    include_package_data=True,
    url='http://packages.python.org/tale',
    license='GPL v3',
    author='Irmen de Jong',
    author_email='irmen@razorvine.net',
    description='Interactive Fiction, MUD & mudlib framework',
    long_description="""Tale is a framework for creating interactive fiction (text adventures), or MUDs (multi-user dungeons).

It's still being developed and new features are implement along the way,
but the current version is quite capable of running an interactive fiction story world.
Also the basics for a multi-user (MUD) server are working nicely.

An example test/demo story is included in the ``stories`` directory of the distribution archive.
This will require you to extract the source archive manually.

You can also run the tiny embedded test story like this, after you've installed the framework::

    $ python -m tale.demo.story

The source code repository is on Github: https://github.com/irmen/Tale
""",
    keywords="mud, mudlib, interactive fiction, text adventure",
    scripts=["scripts/tale-run.cmd", "scripts/tale-run"],
    platforms="any",
    classifiers=[
        "Development Status :: 4 - Beta",
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)"
    ],
    install_requires=["appdirs", "colorama>=0.3.3", "smartypants>=1.8.6"],
    options={"install": {"optimize": 0}}
)

if using_setuptools:
    setup_args["test_suite"] = "tests"

setup(**setup_args)
