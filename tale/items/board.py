"""
Bulletin boards.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""

import datetime
import json
from collections import deque
from typing import Tuple, Dict, Any, Generator, List, Sequence, MutableSequence

from .. import lang, mud_context
from ..base import Item, Living, ParseResult
from ..errors import ActionRefused, ParseError, AsyncDialog, TaleError

__all__ = ["BulletinBoard", "bulletinboard"]


PostType = Dict[str, str]


class BulletinBoard(Item):
    """A bulletin board that stores messages. You can read, post, and remove messages, and reply to them."""
    max_num_posts = 20

    def init(self) -> None:
        super().init()
        self.__posts = deque(maxlen=self.max_num_posts)  # type: MutableSequence[PostType]   # some py 3.5's don't have typing.Deque
        self.readonly = False
        self.storage_file = None  # type: str
        self.verbs = {
            "post": "Write a new message on the board.",
            "write": "Write a new message on the board.",
            "list": "Show the list of messages currently on the board.",
            "read": "Read a specific message on the board (or just the list of messages).",
            "reply": "Write a reply to a message already on the board (indicate the number of the message).",
            "remove": "Remove a message that you wrote earlier (indicate the number of the message)."}

    @property
    def posts(self) -> List[PostType]:
        return list(self.__posts)

    @posts.setter
    def posts(self, value: Sequence[PostType]):
        self.__posts = deque(value, maxlen=self.max_num_posts)

    def allow_item_move(self, actor: Living, verb: str="move") -> None:
        raise ActionRefused("You can't %s %s." % (verb, self.title))

    @property
    def description(self) -> str:
        txt = [self._description]
        if not self.__posts:
            txt.append("It is empty.")
        else:
            if len(self.__posts) == 1:
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

    @description.setter
    def description(self, value: str) -> None:
        raise TaleError("you cannot set the description of a BulletinBoard because it is dynamic")

    def handle_verb(self, parsed: ParseResult, actor: Living) -> bool:
        async_dialog = None
        if parsed.verb == "read":
            if parsed.who_info and self in parsed.who_info:
                self.do_list_messages(actor)
            if parsed.args:
                self.do_read_message(parsed.args[0], actor)
            else:
                return False
        elif parsed.verb == "reply":
            if parsed.who_info and self in parsed.who_info:
                raise ParseError("Reply to which message?")
            if parsed.args:
                async_dialog = self.do_reply_message(parsed.args[0], actor)
            else:
                return False
        elif parsed.verb == "remove":
            if parsed.who_info and self in parsed.who_info:
                raise ParseError("Remove which message?")
            if parsed.args:
                self.do_remove_message(parsed.args[0], actor)
            else:
                return False
        elif parsed.verb in ("post", "write"):
            if not parsed.who_info or self in parsed.who_info:
                async_dialog = self.do_write_message(actor)
            else:
                return False
        elif parsed.verb == "list":
            if not parsed.who_info or self in parsed.who_info:
                self.do_list_messages(actor)
            else:
                return False
        else:
            return False
        if async_dialog:
            raise AsyncDialog(async_dialog)   # @todo yield from not yet possible here
        return True

    def do_list_messages(self, actor: Living) -> None:
        actor.tell_others("{Actor} studies the %s." % self.title)
        actor.tell("You look at the %s." % self.title)
        actor.tell(self._description)
        if not self.__posts:
            actor.tell("It is empty.")
        else:
            if len(self.__posts) == 1:
                actor.tell("There's a message on it:", end=True)
            else:
                actor.tell("There are several messages on it:", end=True)
            txt = ["<ul> # <dim>|</><ul> subject                           <dim>|</><ul> author         <dim>|</><ul> date     </>"]
            for num, post in enumerate(self.__posts, start=1):
                txt.append("%2d.  %-35s %-15s %s" % (num, post["subject"], post["author"], post["date"]))
            actor.tell("\n".join(txt), format=False)

    def _get_post(self, num: str) -> Tuple[int, PostType]:
        if num:
            if num[0] == '#':
                num = num[1:]
            try:
                nr = int(num)
                return nr, self.__posts[nr - 1]
            except ValueError:
                pass
            except IndexError:
                raise ActionRefused("That message doesn't exist.")
        raise ActionRefused("It is unclear what number you mean.")

    def do_write_message(self, actor: Living) -> Generator:
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't write on it.")
        actor.tell_others("{Actor} is writing a message on the %s." % self.title)
        yield from self.dialog_write_message(actor, None)

    def dialog_write_message(self, actor: Living, in_reply_to: PostType=None) -> Generator[Tuple[str, Any], str, None]:
        if in_reply_to:
            subject = "re: {subject}".format(**in_reply_to)
            subject = subject[:50]
            actor.tell("You're replying to the message '{subject}' by {author}, on {date}.".format(**in_reply_to))
            text = "(in reply to '{subject}' by {author} on {date})\n\n".format(**in_reply_to)
        else:
            subject = yield "input", ("Give the subject of your message (max 50 chars):", self._subject_valid)
            subject = subject[:50]
            text = ""
        actor.tell("Please type your message. It can span multiple lines, but can not be longer than 1000 characters. "
                   "Type an empty line or slash ('/') for a paragraph separator, type TWO dots ('..') to end the message.", end=True)
        actor.tell("\n")
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
            actor.tell("<ul>Review your message:</>")
            actor.tell("\n")
            for paragraph in text.split("\n\n"):
                actor.tell(paragraph, end=True)
            if (yield "input", ("\nPost this message?", lang.yesno)):
                post = {
                    "author": actor.name,
                    "date": datetime.datetime.now().date().isoformat(),
                    "subject": subject,
                    "text": text
                }
                self.__posts.appendleft(post)   # type: ignore
                self.save()
                actor.tell("\n")
                actor.tell("You've added the message on top of the list on the %s." % self.name)
                return
        actor.tell("The message is discarded.")

    def _subject_valid(self, subj: str) -> str:
        subj = subj.strip()
        if subj:
            return subj
        raise ValueError("You need to type something.")

    def do_reply_message(self, arg: str, actor: Living) -> Generator:
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't write on it.")
        num, post = self._get_post(arg)
        actor.tell_others("{Actor} is writing a message on the %s." % self.title)
        yield from self.dialog_write_message(actor, post)

    def do_remove_message(self, arg: str, actor: Living) -> None:
        if self.readonly and "wizard" not in actor.privileges:
            raise ActionRefused("You can't remove messages from it.")
        num, post = self._get_post(arg)
        if "wizard" in actor.privileges or actor.name == post["author"]:
            del self.__posts[num - 1]
            actor.tell("You've removed message #%d ('%s') from the board." % (num, post["subject"]))
            actor.tell_others("{Actor} took a message off the %s." % self.title)
            self.save()
        else:
            raise ActionRefused("You cannot remove that message.")

    def do_read_message(self, arg: str, actor: Living) -> None:
        num, post = self._get_post(arg)
        actor.tell_others("{Actor} reads something on the %s." % self.title)
        actor.tell("<ul>Subject: '{subject}' by {author} on {date}. It reads:</>".format(**post), end=True)
        for paragraph in post["text"].split("\n\n"):
            actor.tell(paragraph, end=True)
        return None

    def load(self) -> None:
        """Load persisted messages from the datafile. Note: only the posts are loaded from the datafile, not the descriptive texts"""
        if not self.storage_file:
            return
        try:
            data = json.loads(mud_context.driver.user_resources[self.storage_file].text)
            self.posts = data["posts"]
        except FileNotFoundError:
            pass
        except (ValueError, IOError) as x:
            print("Bulletin board '%s' load error: %s" % (self.name, x))

    def save(self) -> None:
        """save the messages to persistent data file"""
        if not self.storage_file:
            return
        data = {
            "board-name": self.name,
            "board-title": self.title,
            "posts": self.posts
        }
        try:
            mud_context.driver.user_resources[self.storage_file] = json.dumps(data, indent=4, sort_keys=True)
        except IOError as x:
            print("Bulletin board '%s' save error: %s" % (self.name, x))


bulletinboard = BulletinBoard("board", "wooden bulletin board", "The board contains a little plaque: \"important announcements\".",
                              "On a wall, a bulletin board is visible.")
bulletinboard.aliases.add("messages")
bulletinboard.aliases.add("bulletin")
