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

You can run Tale in console mode, where it is a pure text interface running in your
console window. But you can also run Tale in a simple GUI application (built with Tkinter).

.. note::
    The multi-user aspects are on the back burner, I'm mainly focusing on the (single player)
    interactive fiction things right now.

.. note::
    This documentation is still a stub. I hope to write some real documentation soon,
    but in the meantime, use the source, Luke.

Tale can be found on Pypi as `tale <http://pypi.python.org/pypi/tale/>`_.
The source is on Github: https://github.com/irmen/Tale

If you're interested, follow `my blog about developing Tale <http://www.razorvine.net/blog/user/irmen/category/17>`_
(some of the articles are in Dutch but I'll stick to English for the newer ones)


Getting started
---------------
Install tale, preferably using ``pip install tale``. You can also download the source, and then execute ``python setup.py install``.

Tale requires the  `appdirs <http://pypi.python.org/pypi/appdirs/>`_
library to sensibly store data files such as savegames.

After that, you'll need a story to run it on (tale by itself doesn't do anything,
it's only a framework to build games with).
There's a tiny demo embedded in the library itself, you can start that with::

    python -m tale.demo.story   # add --gui to get a GUI interface

Fool around with your pet and try to get out of the house. There's a larger demo story included in the source distribution,
in the ``stories`` directory. But you will have to download and extract the source distribution manually to get it.

Start the demo story using one of the supplied start scripts. You don't have to install Tale first, the script can figure it out.

You can also start it without the script and by using the tale driver directly, but then
it is recommended to properly install tale first. This method of launching stories
won't work from the distribution's root directory itself.

Anyway, the command to do so is::

    $ python -m tale.main --game <path-to-the-story/demo-directory>`

    # or, with the installed launcher script:
    $ tale-run --game <path-to-the-story/demo-directory>`

You can use the ``--help`` argument to see some help about this command.
You can use ``--gui`` to start the GUI version of the interface rather than the text console version.

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
- text console interface or GUI (Tkinter), switchable by command line argument.
- I/O abstraction layer should make it not too hard to make another interface (I'm planning a html/javascript driven one).
- wizard and normal player privileges, wizards gain access to a set of special 'debug' commands that are helpful
  while testing/debugging the game.
- the parser is partly based on a heavily modified adaptation of LPC-MUD's 'soul'
- the soul has 250+ 'emotes' such as bounce and shrug.
- the command line input and the gui version both support tab-completion of commands. (command line requires readline/pyreadline for this)
- it knows 2200+ adverbs that you can use with these emotes. It does prefix matching so you don't have to type
  it out in full (gives a list of suggestions if multiple words match).
- it knows about bodyparts that you can target certain actions (such as kick or pat) at.
- it can deal with object names that consist of multiple words (i.e. contain spaces). For instance, it understands
  when you type 'get the blue pill' when there are multiple pills on the table.
- you can alter the meaning of a sentence by using words like fail, attempt, don't, suddenly, pretend
- you can put stuff into a bag and carry the bag, to avoid cluttering your inventory.
- you can refer to earlier used items and persons by using a pronoun ("examine box / drop it", "examine idiot / slap him").
- yelling something will actually be heard by creatures in adjacent locations. They'll get a message that
  someone is yelling something, and if possible, where the sound is coming from.
- text is nicely formatted when outputted (wrapped to a configurable width).
- uses ansi sequence to spice up the console output a bit (needs colorama on windows, falls back to plain text if not installed)
- uses smartypants if available; to automatically render quotes, dashes, ellipsis etc. in a nicer way. Needs chcp 1252+unicode font on windows.
- game can be saved (and reloaded); pickle is used to serialize the full game world state
- save game data is placed in the operating system's user data directory instead of some random location
- there's a list of 70+ creature races, adapted from the Dead Souls 2 mudlib
- supports two kinds of money: fantasy (gold/silver/copper) and modern (dollars)
- game clock is independent of real-time wall clock, configurable speed and start time
- server 'tick' synced with command entry, or independent. This means things can happen in the background.
- it's trivial to give objects a 'heartbeat' (=they will get a call every server tick to do stuff)
- you can also quite easily schedule calls to be executed at a defined later moment in time
- easy definition of commands in separate functions
- uses docstrings to define command help texts
- command function code is quite compact due to convenient parameters and available methods on the game objects
- command code gets parse information from the soul parser as parameter; very little parsing needs to be done in the command code itself
- there's a set of configurable parameters on a per-story basis
- stories can define their own introduction text and completion texts
- stories can define their own commands or override existing commands
- version checks are done on the story files and the save game files to avoid loading incompatible data
- a lock/unlock/open/close door mechanism is provided with internal door codes to match keys (or key-like objects) against.
- action and event notification mechanism: objects are notified when things happen (such as the player entering a room, or someone saying a line of text) and can react on that.
- hint and story-recap system that can adapt dynamically to the progress of the story.
- contains a simple virtual file system to provide a resource loading / datafile storage facility.
- provides a simple synchronous pubsub/event signaling mechanism
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


API documentation
-----------------

Preliminary (auto-generated) API documentation:

.. toctree::

   api.rst
