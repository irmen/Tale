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
Once Jython's new 2.7 release gets debugged a bit more, it should work on that as well.

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
Install tale, preferably using pip or by executing ``python setup.py install``.

After that, you'll need a story to run it on (tale by itself doesn't do anything,
it's only a framework to build games with).
There's a demo/example story included in the source distribution, in the ``stories`` directory.

Start the demo story using the supplied ``play_demo`` script, or start it using the tale driver directly
(:

:kbd:`$ python -m tale.driver --game <path-to-the-story/demo-directory>`

.. note::
    Running the driver directly and launching a story like this,
    only works correctly after you've actually installed Tale.
    It won't work from the distribution directory.
    (This is because Tale changes its working directory to the directory where
    the story files are located, and they still need to be able to access Tale).

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


