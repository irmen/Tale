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
import json
from http.cookies import SimpleCookie
try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape

__all__ = ["MudHttpIo", "TaleMudWsgiApp"]


class MudHttpIo(HttpIo):
    """
    I/O adapter for a http/browser based interface.
    """
    def __init__(self, player_connection):
        super(MudHttpIo, self).__init__(player_connection)

    def __repr__(self):
        return "<MudHttpIo @ 0x%x>" % id(self)

    def singleplayer_mainloop(self, player_connection):
        raise RuntimeError("this I/O adapter is for multiplayer (mud) mode")

    def pause(self, unpause=False):
        # we'll never pause a mud server.
        pass


class TaleMudWsgiApp(TaleWsgiAppBase):
    def __init__(self, driver):
        super(TaleMudWsgiApp, self).__init__(driver)

    @classmethod
    def create_app_server(cls, driver):
        wsgi_app = SessionMiddleware(cls(driver), MemorySessionFactory())
        wsgi_server = make_server("127.0.0.1", 8180, app=wsgi_app, handler_class=CustomRequestHandler, server_class=CustomWsgiServer)
        wsgi_server.timeout = 0.5
        return wsgi_app, wsgi_server

    def wsgi_handle_start(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        return super(TaleMudWsgiApp, self).wsgi_handle_start(environ, parameters, start_response)

    def wsgi_handle_story(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        return super(TaleMudWsgiApp, self).wsgi_handle_story(environ, parameters, start_response)

    def wsgi_handle_text(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        response = {"text": "sessionid=" + str(session["id"]) + "<br>"}
        return [json.dumps(response).encode("utf-8")]

    def wsgi_handle_tabcomplete(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        return [json.dumps(self.completer.complete(parameters["prefix"])).encode("utf-8")]

    def wsgi_handle_input(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        cmd = parameters.get("cmd", "")
        if cmd and "autocomplete" in parameters:
            suggestions = self.completer.complete(cmd)
            if suggestions:
                self.html_to_browser.append("<p>Suggestions: " + ", ".join(suggestions) + "</p>")
            else:
                self.html_to_browser.append("<p>No matching commands.</p>")
        else:
            cmd = html_escape(cmd, False)
            if cmd:
                self.html_to_browser.append("<span class='txt-userinput'>%s</span>" % cmd)
            self.player_connection.player.store_input_line(cmd)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return []

class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class CustomWsgiServer(WSGIServer):
    request_queue_size = 200


class SessionMiddleware(object):
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
        return self.app(environ, wrapped_start_response)


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
