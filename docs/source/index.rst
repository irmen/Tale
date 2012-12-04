************************************************************
Tale |version| - MUD, mudlib & Interactive Fiction framework
************************************************************

.. image:: _static/tale-large.png
    :align: center
    :alt: Tale logo

What is Tale?
-------------
It is a library for building `Interactive Fiction <http://en.wikipedia.org/wiki/Interactive_fiction>`_,
mudlibs and `muds <http://en.wikipedia.org/wiki/MUD>`_ in Python.

Tale is 100% pure Python and runs on Python 2.7 and 3.2+.
It should also work on Pypy and Ironpython.
Jython 2.5 is not supported, and Jython 2.7 currently has a few bugs that prevent it to run Tale (Jython issues
1886, 1887, 1949, 1994, and probably others). Once these get fixed, Tale should work on Jython 2.7 too.

.. note::
    The multi-user aspects are on the back burner, I'm mainly focusing on the (single player)
    interactive fiction things right now.

.. note::
    This documentation is still a stub. I hope to write some real documentation soon,
    but in the meantime, use the source, Luke.

Tale can be found on Pypi as `tale <http://pypi.python.org/pypi/tale/>`_.
Read only source repository (subversion): ``svn://svn.razorvine.net/Various/Tale``

If you're interested, follow `my blog about developing Tale <http://www.razorvine.net/blog/user/irmen/category/17>`_
(some of the articles are in Dutch but I'll stick to English for the newer ones)


Getting started
---------------
Install tale, preferably using ``pip install tale``. You can also download the source, and then execute ``python setup.py install``.

Tale requires the `blinker <http://pypi.python.org/pypi/blinker/>`_ and `appdirs <http://pypi.python.org/pypi/appdirs/>`_
libraries to be available.

After that, you'll need a story to run it on (tale by itself doesn't do anything,
it's only a framework to build games with).
There's a demo/example story included in the source distribution, in the ``stories`` directory.

Start the demo story using the supplied ``play_demo`` script.
You don't have to install anything if you run it using this script.

You can also start it without the script and by using the tale driver directly, but
it is recommended to properly install it first.
It won't work from the distribution's root directory itself. You need to install Tale properly
and/or invoke it from the start script that belongs to a story.

The command is:

:kbd:`$ python -m tale.driver --game <path-to-the-story/demo-directory>`

The story might prompt you with a couple of questions:
Choose not to load a saved game (you will have none at first start anyway).
Choose to create a default player character or build a custom one. If you choose *wizard privileges*, you
gain access to a whole lot of special wizard commands that can be used to tinker with the internals of the game.

Type :kbd:`help` and :kbd:`help soul` to get an idea of the stuff you can type at the prompt.

You may want to go to the Town Square and say hello to the people standing there::

    >> look

      [Essglen Town square]
      The old town square of Essglen.  It is not much really, and narrow
      streets quickly lead away from the small fountain in the center.
      There's an alley to the south.  A long straight lane leads north towards
      the horizon.
      You see a black gem, a blue gem, a bag, a box1 (a black box), a box2 (a
      white box), a clock, a newspaper, and a trashcan.  Laish the town crier,
      ant, blubbering idiot, and rat are here.

    >> greet laish and the idiot

      You greet Laish the town crier and blubbering idiot.  Laish the town
      crier says: "Hello there, Irmen."  Blubbering idiot drools on you.

    >> recoil

      You recoil with fear.

    >>

Features
--------

A random list of the features of the current codebase:

- Runs on most Python implementations, but requires 2.7 or 3.2+
- game engine and framework code is separated from the actual game code;
  it can run different games from different directories
- single-player I.F. mode and multi-player MUD mode (but no multiplayer server yet,
  it's just a difference in active features for now)
- wizard and normal player privileges, wizards gain access to a set of special 'debug' commands that are helpful
  while testing/debugging the game.
- the parser is partly based on a heavily modified adaptation of LPC-MUD's 'soul'
- the soul has 250+ 'emotes' such as bounce and shrug.
- it knows 2200+ adverbs that you can use with these emotes. It does prefix matching so you don't have to type
  it out in full (gives a list of suggestions if multiple words match).
- it knows about bodyparts that you can target certain actions (such as kick or pat) at.
- it can deal with object names that consist of multiple words (i.e. contain spaces). For instance, it understands
  when you type 'get the blue pill' when there are multiple pills on the table.
- you can alter the meaning of a sentence by using words like fail, attempt, don't, suddenly, pretend
- you can put stuff into a bag and carry the bag, to avoid cluttering your inventory.
- yelling something will actually be heard by creatures in adjacent locations. They'll get a message that
  someone is yelling something, and if possible, where the sound is coming from.
- text is nicely formatted when outputted (wrapped to a configurable width).
- uses colorama if available to spice up the console output a bit.
- game can be saved (and reloaded) - pickle is used to serialize the full game world state
- save game data is placed in the operating system's user data directory
- there's a list of 70+ creature races, adapted from the Dark Souls mudlib
- supports two kinds of money: fantasy (gold/silver/copper) and modern (dollars)
- game clock is independent of real-time wall clock, configurable speed and start time
- server 'tick' synced with command entry, or independent. This means things can happen in the background.
- it's trivial to give objects a 'heartbeat' (=they will get a call every server tick to do stuff)
- you can also quite easily schedule calls to be executed at a defined later moment in time
- easy definition of commands in separate functions
- command function code is quite compact due to convenient parameters and available methods on the game objects
- there's a set of configurable parameters on a per-story basis
- stories can define their own introduction text and completion texts
- stories can define their own commands or override existing commands
- version checks are done on the story files and the save game files to avoid loading data in different versions of the code
- a lock/unlock/open/close door mechanism is provided with internal door codes to match keys (or key-like objects) against.
- action and event notification mechanism: objects are notified when things happen (such as the player entering a room,
  or someone saying a line of text) and can react on that.
- hint and story-recap system that can adapt dynamically to the progress of the story.
- uses the blinker library for internal synchronous signaling (pubsub).
- contains a simple virtual file system to provide a resource loading / datafile storage facility.
- for now, the game object model is object-oriented. You defined objects by instantiating prebuilt classes,
  or derive new classes from them with changed behavior. Currently this means that writing a game is
  very much a programming job. This may or may not improve in the future (to allow for more natural ways
  of writing a game story, in a DSL or whatever).
- many unit tests to validate the code



MUD mode versus Interactive Fiction mode
----------------------------------------
The Tale game driver launches in Interactive Fiction mode by default.
This is because my development efforts are focused on IF at the moment.

However, there's already a bit of multi-user goodness available.
You can enable it by using the :kbd:`--mode mud` command line switch.
A couple of new commands and features are enabled when you do this
(amongst others: message-of-the-day support and the 'stats' command).
Running a IF story in MUD mode may cause some problems. It's only
possible to do this for testing purposes right now.

Currently, there is no actual multi-user support. The Tale game driver
doesn't yet have any multi-user server capabilities, so even in MUD mode,
you're still limited to a single player for now.


Copyright
---------

Tale is copyright © Irmen de Jong (irmen@razorvine.net | http://www.razorvine.net).
It's licensed under GPL v3, see http://www.gnu.org/licenses/gpl.html


