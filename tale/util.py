# coding=utf-8
"""
Utility stuff

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
import datetime
import random
import sys
import functools
import inspect
import traceback
from . import lang
from .errors import ParseError, ActionRefused

if sys.version_info < (3, 0):
    basestring_type = basestring
    import Queue as queue

    def next_iter(iterable):
        return iterable.next()
else:
    basestring_type = str
    import queue

    def next_iter(iterable):
        return next(iterable)


def roll_dice(number=1, sides=6):
    """rolls a number (max 300) of dice with configurable number of sides"""
    assert 1 <= number <= 300
    values = [random.randint(1, sides) for _ in range(number)]
    return sum(values), values


def print_object_location(player, obj, container, print_parentheses=True):
    if not container:
        if print_parentheses:
            player.tell("(It's not clear where %s is)." % obj.name)
        else:
            player.tell("It's not clear where %s is." % obj.name)
        return
    if container in player:
        if print_parentheses:
            player.tell("(%s was found in %s, in your inventory)." % (obj.name, container.title))
        else:
            player.tell("%s was found in %s, in your inventory." % (lang.capital(obj.name), container.title))
    elif container is player.location:
        if print_parentheses:
            player.tell("(%s was found in your current location)." % obj.name)
        else:
            player.tell("%s was found in your current location." % lang.capital(obj.name))
    elif container is player:
        if print_parentheses:
            player.tell("(%s was found in your inventory)." % obj.name)
        else:
            player.tell("%s was found in your inventory." % lang.capital(obj.name))
    else:
        if print_parentheses:
            player.tell("(%s was found in %s)." % (obj.name, container.name))
        else:
            player.tell("%s was found in %s." % (lang.capital(obj.name), container.name))


class MoneyFormatter(object):
    """Display and parsing of money. Supports 'fantasy' and 'modern' style money."""
    money_words_fantasy = {"gold", "silver", "copper", "coppers"}
    money_words_modern = {"dollar", "dollars", "cent", "cents"}

    def __init__(self, money_type):
        if money_type == "fantasy":
            self.display = self.money_display_fantasy
            self.money_to_float = self.money_to_float_fantasy
            self.money_words = self.money_words_fantasy
        elif money_type == "modern":
            self.display = self.money_display_modern
            self.money_to_float = self.money_to_float_modern
            self.money_words = self.money_words_modern
        else:
            raise ValueError("invalid money type " + money_type)

    def money_display_fantasy(self, amount, short=False, zero_msg="nothing"):
        """
        Display amount of money in gold/silver/copper units,
        base unit=silver, 10 silver=1 gold, 0.1 silver=1 copper
        """
        gold, amount = divmod(amount, 10.0)
        silver, copper = divmod(amount, 1.0)
        copper = round(copper * 10.0)
        if short:
            return "%dg/%ds/%dc" % (gold, silver, copper)
        result = []
        if gold:
            result.append("%d gold" % gold)
        if silver:
            result.append("%d silver" % silver)
        if copper:
            result.append("%d copper" % copper)
        if result:
            return lang.join(result)
        return zero_msg

    def money_display_modern(self, amount, short=False, zero_msg="nothing"):
        """
        Display amount of money in modern currency (dollars/cents).
        """
        if short:
            return "$ %.2f" % amount
        dollar, cents = divmod(amount, 1.0)
        cents = round(cents * 100.0)
        result = []
        if dollar:
            result.append("%d " % dollar + lang.pluralize("dollar", dollar))
        if cents:
            result.append("%d " % cents + lang.pluralize("cent", cents))
        if result:
            return lang.join(result)
        return zero_msg

    def money_to_float_fantasy(self, coins):
        """Either a dictionary containing the values per coin type, or a string '11g/22s/33c' is converted to float."""
        if type(coins) is not dict:
            if not coins:
                raise ValueError("That's not an amount of money.")
            result = 0.0
            while coins:
                c, _, coins = coins.partition("/")
                try:
                    if c.endswith("g"):
                        result += float(c[:-1]) * 10.0
                    elif c.endswith("s"):
                        result += float(c[:-1])
                    elif c.endswith("c"):
                        result += float(c[:-1]) / 10.0
                    else:
                        raise ValueError("invalid coin letter")
                except ValueError:
                    raise ValueError("That's not an amount of money.")
            return result
        result = coins.get("gold", 0.0) * 10.0
        result += coins.get("silver", 0.0)
        result += coins.get("copper", 0.0) / 10.0
        result += coins.get("coppers", 0.0) / 10.0
        return result

    def money_to_float_modern(self, coins):
        """Either a dictionary containing the values per coin type, or a string '$1234.55' is converted to float."""
        if type(coins) is not dict:
            if coins.startswith("$"):
                return float(coins[1:])
            else:
                raise ValueError("That's not an amount of money.")
        result = coins.get("dollar", 0.0)
        result += coins.get("dollars", 0.0)
        result += coins.get("cent", 0.0) / 100.0
        result += coins.get("cents", 0.0) / 100.0
        return result

    def parse(self, words):
        """Convert a parsed sequence of words to the amount of money it represents (float)"""
        if len(words) == 1:
            try:
                return self.money_to_float(words[0])
            except ValueError:
                pass
        elif len(words) == 2:
            try:
                return self.money_to_float(words[0] + words[1])
            except ValueError:
                pass
        coins = {}
        if set(words) & self.money_words:
            # check if all words are either a number (currency) or a money word
            amount = None
            for word in words:
                if word in self.money_words:
                    if amount:
                        if word in coins:
                            raise ParseError("What amount?")
                        coins[word] = amount
                        amount = None
                    else:
                        raise ParseError("What amount?")
                else:
                    try:
                        amount = float(word)
                    except ValueError:
                        raise ParseError("What amount?")
            return self.money_to_float(coins)
        raise ParseError("That is not an amount of money.")


def parse_time(args):
    """parses a time from args like: 13:44:59, or like a duration such as 1h 30m 15s"""
    try:
        duration = parse_duration(args)
        return (datetime.datetime.min + duration).time()
    except ParseError:
        if not args or len(args) > 1:
            raise ParseError("It's not clear what time you mean.")
        try:
            return datetime.datetime.strptime(args[0], "%H:%M:%S").time()
        except ValueError:
            try:
                return datetime.datetime.strptime(args[0], "%H:%M").time()
            except ValueError:
                if args[0] == "noon":
                    return datetime.time(hour=12)
                elif args[0] == "midnight":
                    return datetime.time(hour=0)
                elif args[0] in ("sunrise", "dawn"):
                    return datetime.time(hour=6)
                elif args[0] in ("sunset", "dusk"):
                    return datetime.time(hour=20)
                elif args[0] in ("evening", "morning", "later", "earlier", "future", "past"):
                    raise ParseError("You must be more specific about the time you mean.")
                else:
                    raise ParseError("It's not clear what time you mean.")


def parse_duration(args):
    """parses a duration from args like: 1 hour 20 minutes 15 seconds (hour/h, minutes/min/m, seconds/sec/s)"""
    hours = minutes = seconds = 0
    if args:
        number = None
        for arg in args:
            if len(arg) >= 2 and arg.endswith(("h", "m", "s")):
                try:
                    if arg[-1] == "h":
                        hours = int(arg[:-1])
                    elif arg[-1] == "m":
                        minutes = int(arg[:-1])
                    elif arg[-1] == "s":
                        seconds = int(arg[:-1])
                    continue
                except ValueError:
                    pass
            if arg in ("hours", "hour", "h"):
                hours = number
                number = None
            elif arg in ("minutes", "minute", "min", "m"):
                minutes = number
                number = None
            elif arg in ("seconds", "second", "sec", "s"):
                seconds = number
                number = None
            else:
                try:
                    number = float(arg)
                except ValueError:
                    raise ParseError("It's not clear what duration you mean.")
    if hours == minutes == seconds == 0:
        raise ParseError("It's not clear what duration you mean.")
    try:
        return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except TypeError:
        raise ParseError("It's not clear what duration you mean.")


def duration_display(duration):
    secs = duration.total_seconds()
    if secs == 0:
        return "no time at all"
    hours, secs = divmod(secs, 3600)
    minutes, secs = divmod(secs, 60)
    result = []
    if hours == 1:
        result.append("1 hour")
    elif hours > 1:
        result.append("%d hours" % hours)
    if minutes == 1:
        result.append("1 minute")
    elif minutes > 1:
        result.append("%d minutes" % minutes)
    if secs == 1:
        result.append("1 second")
    elif secs > 1:
        result.append("%d seconds" % secs)
    return lang.join(result)


def format_docstring(docstring):
    """Format a docstring according to the algorithm in PEP-257"""
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def storyname_to_filename(name):
    """converts the story name to a suitable name for a file on disk"""
    filename = name.lower()
    filename = filename.replace(" ", "_")
    filename = filename.replace(".", "_")
    filename = filename.replace("'", "")
    filename = filename.replace('"', "")
    filename = filename.replace("\\", "")
    filename = filename.replace("/", "")
    filename = filename.replace("*", "")
    return filename


class GameDateTime(object):
    """
    The datetime class that tracks game time.
    times_realtime means how much faster the game time is running than real time.
    The internal 'clock' tracks the time in game-time (not real-time).
    """
    def __init__(self, date_time, times_realtime=1):
        assert times_realtime >= 0
        self.times_realtime = times_realtime
        self.clock = date_time

    def __str__(self):
        return str(self.clock)

    def add_gametime(self, timedelta):
        """advance the game clock by a time delta expressed in game time"""
        assert isinstance(timedelta, datetime.timedelta)
        self.clock += timedelta

    def sub_gametime(self, timedelta):
        """rewind the game clock by a time delta expressed in game time"""
        assert isinstance(timedelta, datetime.timedelta)
        self.clock -= timedelta

    def plus_realtime(self, timedelta):
        """return the game clock plus a time delta expressed in real time"""
        assert isinstance(timedelta, datetime.timedelta)
        return self.clock + timedelta * self.times_realtime

    def minus_realtime(self, timedelta):
        """return the game clock minus a time delta expressed in real time"""
        assert isinstance(timedelta, datetime.timedelta)
        return self.clock - timedelta * self.times_realtime

    def add_realtime(self, timedelta):
        """advance the game clock by a time delta expressed in real time"""
        assert isinstance(timedelta, datetime.timedelta)
        self.clock += timedelta * self.times_realtime

    def sub_realtime(self, timedelta):
        """rewind the game clock by a time delta expressed in real time"""
        assert isinstance(timedelta, datetime.timedelta)
        self.clock -= timedelta * self.times_realtime


class Context(object):
    """
    A new instance of this context is passed to every command function and obj.destroy.
    Note that the player object isn't in here because it is already explicitly passed to these functions.
    """
    def __init__(self, driver, clock, config, player_connection):
        self.driver = driver
        self.clock = clock
        self.config = config
        self.conn = player_connection

    def __eq__(self, other):
        return vars(self) == vars(other)


def authorized(*privileges):
    """
    Decorator for callables that need a privilege check.
    The callable should have an 'actor' argument that is passed an
    appropriate actor object with .privileges to check against.
    If they don't match with the privileges given in this decorator,
    an ActionRefused error is raised.
    """
    def checked(f):
        if "actor" not in inspect.getargspec(f).args:
            raise SyntaxError("callable requires 'actor' argument: " + f.__name__)
        allowed_privs = set(privileges)

        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # check if the supplied actor
            actor = inspect.getcallargs(f, *args, **kwargs)["actor"]
            try:
                if actor and allowed_privs & actor.privileges:
                    return f(*args, **kwargs)
            except AttributeError:
                # actors without .privileges, are also not allowed to do anything
                pass
            raise ActionRefused("You're not allowed to do that.")
        return wrapped
    if not privileges:
        raise ValueError("privileges must contain at least one value")
    return checked


def search_item(name, collection):
    """
    Searches an item (by name) in a collection of Items.
    Returns the first match. Also considers aliases and titles.
    """
    name = name.lower()
    items = [i for i in collection if i.name == name]
    if not items:
        # try the aliases or titles
        items = [i for i in collection if name in i.aliases or i.title.lower() == name]
    return items[0] if items else None


def sorted_by_name(stuff):
    return sorted(stuff, key=lambda thing: thing.name.lower())


def formatTraceback(ex_type=None, ex_value=None, ex_tb=None, detailed=True, withSelf=False):
    """Formats an exception traceback. If you ask for detailed formatting,
    the result will contain info on the variables in each stack frame.
    You don't have to provide the exception info objects, if you omit them,
    this function will obtain them itself using ``sys.exc_info()``."""
    if ex_type is not None and ex_value is None and ex_tb is None:
        # possible old (3.x) call syntax where caller is only providing exception object
        if type(ex_type) is not type:
            raise TypeError("invalid argument: ex_type should be an exception type, or just supply no arguments at all")
    width = 55
    result = ["\n\n", "-" * width + "\n", " CRASH OCCURRED! TIMESTAMP: %s\n" % datetime.datetime.now()]
    if ex_type is None and ex_tb is None:
        ex_type, ex_value, ex_tb = sys.exc_info()
    if detailed and sys.platform != "cli":  # detailed tracebacks don't work in ironpython (most of the local vars are omitted)
        def makeStrValue(value):
            try:
                return repr(value)
            except:
                try:
                    return str(value)
                except:
                    return "<ERROR>"

        import linecache
        try:
            result.append("-" * width + "\n")
            result.append(" EXCEPTION: %s\n" % ex_type.__name__)
            result.append(" MESSAGE: %s\n" % ex_value)
            result.append(" Extended stacktrace follows (most recent call last):\n")
            skipLocals = True  # don't print the locals of the very first stack frame
            while ex_tb:
                frame = ex_tb.tb_frame
                sourceFileName = frame.f_code.co_filename
                if "self" in frame.f_locals:
                    location = "%s.%s" % (frame.f_locals["self"].__class__.__name__, frame.f_code.co_name)
                else:
                    location = frame.f_code.co_name
                result.append("   ----\n")
                result.append("File \"%s\", line %d, in %s\n" % (sourceFileName, ex_tb.tb_lineno, location))
                result.append("Source code:\n")
                result.append("    " + linecache.getline(sourceFileName, ex_tb.tb_lineno).strip() + "\n")
                if not skipLocals:
                    names = set()
                    names.update(getattr(frame.f_code, "co_varnames", ()))
                    names.update(getattr(frame.f_code, "co_names", ()))
                    names.update(getattr(frame.f_code, "co_cellvars", ()))
                    names.update(getattr(frame.f_code, "co_freevars", ()))
                    result.append("Local values:\n")
                    for name2 in sorted(names):
                        if name2 in frame.f_locals:
                            value = frame.f_locals[name2]
                            result.append("    %s = %s\n" % (name2, makeStrValue(value)))
                            if name2 == "self" and withSelf:
                                # print the local variables of the class instance
                                for name3, value in vars(value).items():
                                    result.append("        self.%s = %s\n" % (name3, makeStrValue(value)))
                skipLocals = False
                ex_tb = ex_tb.tb_next
            result.append("\n EXCEPTION HERE: %s: %s\n" % (ex_type.__name__, ex_value))
            result.append("-" * width + "\n")
            return result
        except Exception:
            result.extend(
                 ["-" * width + "\nError building extended traceback!!! :\n",
                  "".join(traceback.format_exception(*sys.exc_info())) + '-' * width + '\n',
                  "Original Exception follows:\n",
                  "".join(traceback.format_exception(ex_type, ex_value, ex_tb))])
            return result
    else:
        # default traceback format.
        result.extend(traceback.format_exception(ex_type, ex_value, ex_tb))
        result.append("-" * width + "\n")
        return result


def excepthook(ex_type, ex_value, ex_tb):
    """An exception hook you can use for ``sys.excepthook``, to automatically print detailed tracebacks"""
    traceback = "".join(formatTraceback(ex_type, ex_value, ex_tb, detailed=True, withSelf=False))
    sys.stderr.write(traceback)
