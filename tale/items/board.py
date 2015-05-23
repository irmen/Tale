# coding=utf-8
"""
Bulletin boards.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from ..base import Item
from ..errors import ActionRefused, ParseError
import datetime


__all__ = ["BulletinBoard", "bulletinboard"]


class BulletinBoard(Item):
    class Post(object):
        def __init__(self, author, date, subject, text):
            self.author = author
            self.date = date
            self.subject = subject.strip()
            self.text = text.strip()

    def init(self):
        super(BulletinBoard, self).init()
        self.posts = []
        self.max_num_posts = 20
        self.verbs = {
            "post": "write a new message on the board",
            "write": "write a new message on the board",
            "list": "show the list of messages currently on the board",
            "read": "read a specific message on the board (or just the list of messages)",
            "reply": "write a reply to a message already on the board",
            "remove": "remove a message that you wrote earlier"}
        self.readonly = False

    def allow_item_move(self, actor, verb="move"):
        raise ActionRefused("You can't %s %s." % (verb, self.title))

    @property
    def description(self):
        txt = [self._description]
        if not self.posts:
            txt.append("It is empty.")
        else:
            if len(self.posts) == 1:
                txt.append("There's a message on it.")
            else:
                txt.append("There are several messages on it.")
            txt.append("You can 'list' the messages, or 'read 3' to read the third in the list. ")
        txt.append("You can 'post' or 'write' a new message, 'reply 3' to write a reply to the third in the list.")
        txt.append("Finally it is possible to use 'remove 3' to remove the third in the list (only if you wrote it).")
        return "\n".join(txt)

    def handle_verb(self, parsed, actor):
        if parsed.verb == "read":
            if parsed.who_info and self in parsed.who_info:
                self.do_list_messages(actor)
                return True
            if parsed.args:
                self.do_read_message(parsed.args[0], actor)
                return True
        elif parsed.verb == "reply":
            if parsed.who_info and self in parsed.who_info:
                raise ParseError("Reply to which message?")
            if parsed.args:
                self.do_reply_message(parsed.args[0], actor)
                return True
        elif parsed.verb == "remove":
            if parsed.who_info and self in parsed.who_info:
                raise ParseError("Remove which message?")
            if parsed.args:
                self.do_remove_message(parsed.args[0], actor)
                return True
        elif parsed.verb in ("post", "write"):
            if not parsed.who_info or self in parsed.who_info:
                self.do_write_message(actor)
                return True
        elif parsed.verb == "list":
            if not parsed.who_info or self in parsed.who_info:
                self.do_list_messages(actor)
                return True
        return False

    def do_list_messages(self, actor):
        actor.tell_others("{Title} studies the %s." % self.title)
        actor.tell("You look at the %s." % self.title)
        actor.tell(self._description)
        if not self.posts:
            actor.tell("It is empty.")
        else:
            if len(self.posts) == 1:
                actor.tell("There's a message on it:", end=True)
            else:
                actor.tell("There are several messages on it:", end=True)
            txt = ["<ul> # <dim>|</><ul> subject                           <dim>|</><ul> author         <dim>|</><ul> date     </>"]
            for num, post in enumerate(self.posts, start=1):
                txt.append("%2d.  %-35s %-15s %s" % (num, post.subject, post.author, post.date))
            actor.tell(*txt, format=False)

    def _get_post(self, num):
        if num:
            if num[0] == '#':
                num = num[1:]
            try:
                num = int(num)
                return num, self.posts[num - 1]
            except ValueError:
                pass
            except IndexError:
                raise ActionRefused("That message doesn't exist.")
        raise ActionRefused("It is unclear what number you mean.")

    def do_write_message(self, actor):
        actor.tell_others("{Title} is writing a message on the %s." % self.title)
        print("@todo dialog WRITE MSG") # XXX

    def do_reply_message(self, arg, actor):
        num = self._get_post(arg)
        actor.tell_others("{Title} is writing a message on the %s." % self.title)
        print("@todo dialog REPLY MSG", num) # XXX

    def do_remove_message(self, arg, actor):
        num, post = self._get_post(arg)
        if "wizard" in actor.privileges or actor.name == post.author:
            del self.posts[num - 1]
            actor.tell("You've removed message #%d from the board." % num)
            actor.tell_others("{Title} took a message off the %s." % self.title)
        else:
            raise ActionRefused("You cannot remove that message.")

    def do_read_message(self, arg, actor):
        num, post = self._get_post(arg)
        actor.tell_others("{Title} reads something on the %s." % self.title)
        actor.tell("The message is titled '%s'." % post.subject)
        actor.tell("It was written by %s on %s, and it reads:" % (post.author, post.date), end=True)
        actor.tell("\n")
        for paragraph in post.text.split("\n\n"):
            actor.tell(paragraph, end=True)


bulletinboard = BulletinBoard("board", "wooden bulletin board", "It displays: \"important announcements\".", "On a wall, a bulletin board is visible.")
bulletinboard.posts = [
    BulletinBoard.Post("irmen", datetime.datetime.now().date(), "hello and welcome to the mud", "Hello all who read this! Welcome to the mud"),
    BulletinBoard.Post("irmen", datetime.datetime.now().date(), "behavior", "Please behave responsibly.\n\nSigned, Irmen")
]
