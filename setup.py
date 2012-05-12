from distutils.core import setup

setup(
    name='tale',
    version='0.3',
    packages=['tale', 'tale.cmds', 'tale.items', 'tale.messages', 'tale.rooms'],
    package_data={
        'tale': ['soul_adverbs.txt', 'messages/*']
        },
    url='http://irmen.home.xs4all.nl/tale/',
    license='GPL v3',
    author='Irmen de Jong',
    author_email='irmen@razorvine.net',
    description='Mud, mudlib & interactive fiction framework',
    long_description="""Tale is a framework for creating mudlibs, muds and/or interactive fiction (text adventures).""",
    keywords="mud, mudlib, interactive fiction, text adventure",
    scripts=[],
    platforms="any",
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
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
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)"
    ]
)
