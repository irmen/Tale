Adding type hints to Tale
-------------------------

Intro
-----

'Tale - an Interactive Fiction, MUD & mudlib framework' is
a medium sized Python project. At the time of writing (just after 
releasing version 3.1 of the project), 
it has about 15000 SLOC (~9500 in the tale library, 
~3800 in the test suite, and ~2100 in the demo stories).

You can find it on Github; https://github.com/irmen/Tale

Tale started as a Python 2.x-and-3.x compatible library but I decided
I want to be able to use modern Python (3.5+) features and not worry
anymore about backwards compatibility, so I cleaned up and modernized the code a while ago.

After finishing that, one of the major new Python features I still hadn't used anywhere,
was _type hinting_. Because I wanted to learn to use it, I took Tale as
a test case and added type hints to all of the code.
I wanted to learn about the syntax,
how to apply it to an existing code base,
to see what benefits it gives,
and to discover what problems it introduces and what limitations it has.

Below are the results.


Benefits
--------

The following things have proven to be beneficial to me:

- PyCharm (my IDE of choice) is giving more detailed warning messages and code completion suggestions:
  it adds inferred types or type hints to it.
- The MyPy tool (http://mypy.readthedocs.io/en/latest/index.html) is able to statically find type related errors in the code 
  at _compile time_ rather than having to run into them during _run time_.
  It correctly identified several mistakes that were in the code that I had 
  not discovered yet and weren't caught by the unit tests.
- Mypy is pretty smart, I was quite surprised by its capability to infer
  the type of things and how it propagates through the code.
- Type hinting is optional so you can mix code with and without type hints.
 


Things I'm not happy with
-------------------------

- It takes a lot of effort to add correct type hints everywhere.
  Before this task is complete, mypy can and will report lots of
  errors that are wrong or can be misleading.

- Mypy has bugs. One of the most obvious is that it doesn't know about
  several modules and classes from the standard library.

- Shutting mypy up is done via a `# type: ignore` comment.
  Tale now has about 60 of these...
  Some of them can and should be removed once mypy gets smarter,
  but I have no way of knowing which ones they are. How am I going to maintain these?
  It strongly reminds me of the 'suppress-warning' type of comments found
  in other languages.  This is problematic because it hides possible errors
  in a way that is hard to find later.
  
- I really don't like these two major aspects of the type hint syntax:
    1. Sometimes you have to use _strings_ rather than the type itself.
       This is because the hints are parsed at the same time as all other code,
       and sometimes you need "forward references" to types that are not yet defined.
       This can sometimes be fixed by rearranging the definition order
       of your classes, but if classes reference each other (which is common)
       this doesn't help. I find the most irritating that you have to
       do this for the actual class that you're type hinting the methods of!
       I understand the reason (the class is still being parsed, and is not 
       yet _defined_) but I find it very cumbersome.     
    2. Type hints for variables are often required to help mypy. Especially
       if you're initializing names with empty collection types such as `[]` or `{}`
       which is common.  Also you have to do this via a _comment_ such as `# type: List[str]`
       The latter is improved in Python 3.6 (see PEP-526) but I want to 
       stick with 3.5 as a minimum for a while.
       
       
- Because type hints are parsed by Python itself, and because mypy 
  even parses the comments as well,
  you'll have to import all types that you use in hints. 
  This causes a lot of extra imports in every module.
  In my case this even led to some circular import problems that
  were only fixable by changing the modules itself. (One can argue
  that this is a good thing! Because circular references often
  are a code smell)
  Some types are only used in a _comment_, which 
  causes the IDE to warn me about unused imports that it wants to
  clean up (but if I do this, it breaks mypy). PyCharm is not (yet)
  smart enough to see that an import is really used even if it is just a type hint comment.
  To be honest, PyCharm has a point, because it is *mypy* that uses it, not *python*...
  But it causes me to have to accept several warnings that aren't.

- The code becomes harder to read. In some cases, _a lot harder_ because
  some type hints can become quite elaborate (list of dicts mapping str to tuple... etc)
  You can ease the pain a bit by creating your own type classes but
  this clutters the module namespace.



Things learned, thougts
-----------------------

After adding type hints to all of Tale's code, a lot of time
was spent fixing mistakes (in the hints I wrote) and several bugs (that mypy found).

After all of this, I learned that
- using type hints helps uncover bugs and improves IDE feedback and code understanding
- it is quite a lot of work to add it to an existing code base and "get it right" (= no mypy errors)
- it has to be done in an 'unnatural' way sometimes, because of the way Python parses stuff
- it can clutter up code that was very concise and clean before.


But the most important thing really:

_...static typing (via type hints + mypy tooling) clashes with Python's dynamic duck type nature._
It all still feels 'off' to me, in the context of Python. It introduces new kinds of problems, that we didn't have
without them, and the syntax is not as 'natural' as I hoped.

Right now, I am not really sure if I want to continue to use type hints.
In Tale I probably will because it now has them everywhere already, but 
my other projects have to wait.

As this is the first and only time so far that I have used type hints,
it is very likely that I made some mistakes or missed a better solution to 
some of the issues I encountered.
Please correct me on them or give me some tips on improving my application
and understanding of Python's type hints. Thank you!
