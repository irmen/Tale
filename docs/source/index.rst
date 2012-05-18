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
    This documentation is still a stub. I hope to write some real documentation soon,
    but in the meantime, use the source, Luke.


Getting started
---------------
Quickstart:
Run the included test world by starting the driver:

:kbd:`$ python -m tale.driver`   (or use the supplied :kbd:`tale-driver` launch script)

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


Copyright
---------

Tale is copyright © Irmen de Jong (irmen@razorvine.net | http://www.razorvine.net).
It's licensed under GPL v3 (see ``LICENSE.txt``).

Tale can be found on Pypi as `tale <http://pypi.python.org/pypi/tale/>`_.


