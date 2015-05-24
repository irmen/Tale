# coding=utf-8
"""
Bulletin boards.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

from __future__ import absolute_import, print_function, division, unicode_literals
from ..base import Item
from ..errors import ActionRefused, ParseError, AsyncDialog
from .. import lang, mud_context
import json
import datetime

__all__ = ["BulletinBoard", "bulletinboard"]


class BulletinBoard(Item):
    def init(self):
        super(BulletinBoard, self).init()
        self.posts = []
        self.max_num_posts = 20
        self.readonly = False
        self.storage_file = None
        self.verbs = {
            "post": "Write a new message on the board.",
            "write": "Write a new message on the board.",
            "list": "Show the list of messages currently on the board.",
            "read": "Read a specific message on the board (or just the list of messages).",
            "reply": "Write a reply to a message already on the board (indicate the number of the message).",
            "remove": "Remove a message that you wrote earlier (indicate the number of the message)."}

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
        if self.readonly:
            txt.append("It seems like it's not possible to change anything on the %s." % self.name)
        else:
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
                txt.append("%2d.  %-35s %-15s %s" % (num, post["subject"], post["author"], post["date"]))
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
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't write on it.")
        actor.tell_others("{Title} is writing a message on the %s." % self.title)
        raise AsyncDialog(self.dialog_write_message(actor, None))

    def dialog_write_message(self, actor, in_reply_to=None):
        if in_reply_to:
            subject = "re: {subject}".format(**in_reply_to)
            subject = subject[:50]
            actor.tell("You're replying to the message '{subject}' by {author}, on {date}.".format(**in_reply_to))
            text = ["(in reply to '{subject}' by {author} on {date})".format(**in_reply_to), "\n"]
        else:
            subject = yield "input", ("Give the subject of your message (max 50 chars):", self._subject_valid)
            subject = subject[:50]
            text = []
        actor.tell("Please type your message. It can span multiple lines, but can not be longer than 1000 characters. "
                   "Type an empty line or slash ('/') for a paragraph separator, type TWO dots ('..') to end the message.", end=True)
        actor.tell("\n")
        text = ""
        while len(text) <= 1000:
            line = yield "input", None
            if line == "..":
                break
            if line == "/":
                line = ""
            text += line.strip() + "\n"
        text = text.strip()
        if text:
            actor.tell("\n")
            actor.tell("<ul>Review your message:</>", end=True)
            for paragraph in text.split("\n\n"):
                actor.tell(paragraph, end=True)
            if (yield "input", ("Post this message?", lang.yesno)):
                post = {
                    "author": actor.name,
                    "date": datetime.datetime.now().date().isoformat(),
                    "subject": subject,
                    "text": text
                }
                self.posts.insert(0, post)
                self.posts = self.posts[:self.max_num_posts]
                self.save()
                actor.tell("\n")
                actor.tell("You've added the message on top of the list on the %s." % self.name)
                return
        actor.tell("The message is discarded.")

    def _subject_valid(self, subj):
        subj = subj.strip()
        if subj:
            return subj
        raise ValueError("You need to type something.")

    def do_reply_message(self, arg, actor):
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't write on it.")
        num, post = self._get_post(arg)
        actor.tell_others("{Title} is writing a message on the %s." % self.title)
        raise AsyncDialog(self.dialog_write_message(actor, post))

    def do_remove_message(self, arg, actor):
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't remove messages from it.")
        num, post = self._get_post(arg)
        if "wizard" in actor.privileges or actor.name == post["author"]:
            del self.posts[num - 1]
            actor.tell("You've removed message #%d ('%s') from the board." % (num, post["subject"]))
            actor.tell_others("{Title} took a message off the %s." % self.title)
            self.save()
        else:
            raise ActionRefused("You cannot remove that message.")

    def do_read_message(self, arg, actor):
        num, post = self._get_post(arg)
        actor.tell_others("{Title} reads something on the %s." % self.title)
        actor.tell("<ul>Subject: '{subject}' by {author} on {date}. It reads:</>".format(**post), end=True)
        for paragraph in post["text"].split("\n\n"):
            actor.tell(paragraph, end=True)

    def load(self):
        """Load persisted messages from the datafile. Note: only the posts are loaded from the datafile, not the descriptive texts"""
        if not self.storage_file:
            return
        try:
            data = json.loads(mud_context.driver.user_resources[self.storage_file].data.decode("UTF-8"))
            self.posts = data["posts"][:self.max_num_posts]
        except IOError:
            pass

    def save(self):
        """save the messages to persistent data file"""
        if not self.storage_file:
            return
        data = {
            "board-name": self.name,
            "board-title": self.title,
            "posts": self.posts
        }
        mud_context.driver.user_resources[self.storage_file] = json.dumps(data, indent=4, sort_keys=True).encode("UTF-8")


bulletinboard = BulletinBoard("board", "wooden bulletin board", "The board contains a little plaque: \"important announcements\".",
                              "On a wall, a bulletin board is visible.")
bulletinboard.aliases.add("messages")
bulletinboard.aliases.add("bulletin")
