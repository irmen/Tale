# coding=utf-8
"""
Webbrowser based I/O for a multi player ('mud') server.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division
from .if_browser_io import HttpIo, TaleWsgiAppBase
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
import time
import random
import sys
import hashlib
try:
    from http.cookies import SimpleCookie
except ImportError:
    from Cookie import SimpleCookie
try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape
from . import vfs
from .. import __version__ as tale_version_str

__all__ = ["MudHttpIo", "TaleMudWsgiApp"]


class MudHttpIo(HttpIo):
    """
    I/O adapter for a http/browser based interface.
    """
    def __init__(self, player_connection):
        super(MudHttpIo, self).__init__(player_connection, None)
        self.supports_blocking_input = False

    def __repr__(self):
        return "<MudHttpIo @ 0x%x>" % id(self)

    def singleplayer_mainloop(self, player_connection):
        raise RuntimeError("this I/O adapter is for multiplayer (mud) mode")

    def pause(self, unpause=False):
        # we'll never pause a mud server.
        pass


class TaleMudWsgiApp(TaleWsgiAppBase):
    """
    The actual wsgi app that the player's browser connects to.
    This one is capable of dealing with multiple connected clients (multi-player).
    """
    def __init__(self, driver):
        super(TaleMudWsgiApp, self).__init__(driver)

    @classmethod
    def create_app_server(cls, driver):
        wsgi_app = SessionMiddleware(cls(driver), MemorySessionFactory())
        wsgi_server = make_server("127.0.0.1", 8180, app=wsgi_app, handler_class=CustomRequestHandler, server_class=CustomWsgiServer)
        return wsgi_server

    def wsgi_handle_story(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        if "player_connection" not in session:
            # create a new connection
            conn = self.driver._connect_mud_player()
            session["player_connection"] = conn
        return super(TaleMudWsgiApp, self).wsgi_handle_story(environ, parameters, start_response)

    def wsgi_handle_text(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        conn = session.get("player_connection")
        if not conn:
            return self.wsgi_internal_server_error(start_response, "not logged in")
        if not conn or not conn.player or not conn.io:
            raise SessionMiddleware.CloseSession("no longer a valid connection")
        return super(TaleMudWsgiApp, self).wsgi_handle_text(environ, parameters, start_response)

    def wsgi_handle_quit(self, environ, parameters, start_response):
        # Quit/logged out page. For multi player, get rid of the player connection.
        # @todo auto clean up session and connection when player disconnected (= hasn't done a request in X time)
        session = environ["wsgi.session"]
        conn = session.get("player_connection")
        if not conn:
            return self.wsgi_internal_server_error(start_response, "not logged in")
        if conn.player:
            self.driver._disconnect_mud_player(conn)
        raise SessionMiddleware.CloseSession("<html><body><script>window.close();</script>Session ended. You may close this window/tab.</body></html>")

    def wsgi_handle_about(self, environ, parameters, start_response):
        # about page
        start_response("200 OK", [('Content-Type', 'text/html; charset=utf-8')])
        resource = vfs.internal_resources["web/about_mud.html"]
        player_table = ["<br><p><em>Connected players:</em></p><pre>"]
        for name, conn in self.driver.all_players.items():
            player_table.append(html_escape("Name:  %s   connection: %s" % (name, conn.io)))
        player_table.append("</pre>")
        player_table = "\n".join(player_table)
        txt = resource.data.format(tale_version=tale_version_str,
                                   story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   uptime="%d:%02d:%02d" % self.driver.uptime,
                                   starttime=self.driver.server_started,
                                   num_players=len(self.driver.all_players),
                                   player_table=player_table)
        return [txt.encode("utf-8")]


class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class CustomWsgiServer(WSGIServer):
    request_queue_size = 200


class SessionMiddleware(object):

    class CloseSession(Exception):
        """
        Raise this from your wsgi function to remove the current session.
        The exception message is returned as last goodbye text to the browser.
        """
        pass

    def __init__(self, app, factory):
        self.app = app
        self.factory = factory

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if not path.startswith("/tale/"):
            # paths not under /tale/ won't get a session
            return self.app(environ, start_response)

        cookie = SimpleCookie()
        if 'HTTP_COOKIE' in environ:
            cookie.load(environ['HTTP_COOKIE'])
        sid = None
        if "session_id" in cookie:
            sid = cookie["session_id"].value
        environ["wsgi.session"] = self.factory.load(sid)

        def wrapped_start_response(status, response_headers, exc_info=None):
            sid = self.factory.save(environ["wsgi.session"])
            cookies = SimpleCookie()
            cookies["session_id"] = sid
            cookie = cookies["session_id"]
            cookie["path"] = "/tale"
            cookie["httponly"] = 1
            response_headers.extend(("set-cookie", morsel.OutputString()) for morsel in cookies.values())
            return start_response(status, response_headers, exc_info)

        try:
            return self.app(environ, wrapped_start_response)
        except SessionMiddleware.CloseSession as x:
            self.factory.delete(sid)
            # clear the browser cookie
            cookies = SimpleCookie()
            cookies["session_id"] = "deleted"
            cookie = cookies["session_id"]
            cookie["path"] = "/tale"
            cookie["httponly"] = 1
            cookie["expires"] = "Thu, 01-Jan-1970 00:00:00 GMT"
            response_headers = [('Content-Type', 'text/html')]
            response_headers.extend(("set-cookie", morsel.OutputString()) for morsel in cookies.values())
            start_response("200 OK", response_headers)
            return [str(x).encode("utf-8")]


class MemorySessionFactory(object):
    def __init__(self):
        self.storage = {}

    def generate_id(self):
        string = "%d%d%f" % (random.randint(0, sys.maxsize), id(self), time.time())
        return hashlib.sha1(string.encode("ascii")).hexdigest()

    def load(self, sid):
        sid = sid or self.generate_id()
        if sid not in self.storage:
            session = {
                "id": sid,
                "created": time.time()
            }
            self.storage[sid] = session
        return self.storage[sid]

    def save(self, session):
        session["id"] = sid = session["id"] or self.generate_id()
        self.storage[sid] = session
        return sid

    def delete(self, sid):
        if sid in self.storage:
            del self.storage[sid]
