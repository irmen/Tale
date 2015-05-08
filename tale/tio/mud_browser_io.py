# coding=utf-8
"""
Webbrowser based I/O for a multi player ('mud') server.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division
from .if_browser_io import HttpIo, TaleWsgiAppBase
from . import vfs
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
import time
from http.cookies import SimpleCookie

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
        wsgi_app = cls(driver)
        wsgi_server = make_server("localhost", 8180, app=wsgi_app, handler_class=CustomRequestHandler, server_class=CustomWsgiServer)
        wsgi_server.timeout = 0.5
        return wsgi_app, wsgi_server

    def wsgi_route(self, environ, path, parameters, start_response):
        if path == "login":
            return self.wsgi_handle_login(environ, parameters, start_response)
        elif path == "logout":
            return self.wsgi_handle_logout(environ, parameters, start_response)
        return super(TaleMudWsgiApp, self).wsgi_route(environ, path, parameters, start_response)

    def wsgi_handle_start(self, environ, parameters, start_response):
        # start page / titlepage
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        etag = self.etag(id(self), time.mktime(self.driver.server_started.timetuple()), "start")
        if_none = environ.get('HTTP_IF_NONE_MATCH')
        if if_none and (if_none == '*' or etag in if_none):
            return self.wsgi_not_modified(start_response)
        headers.append(("ETag", etag))
        start_response("200 OK", headers)
        resource = vfs.internal_resources["web/index.html"]
        txt = resource.data.format(story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   story_author=self.driver.config.author,
                                   story_author_email=self.driver.config.author_address)
        return [txt.encode("utf-8")]

    def wsgi_handle_story(self, environ, parameters, start_response):
        # generate session cookie if not present
        cookies = SimpleCookie()
        session_id = None
        if "HTTP_COOKIE" in environ:
            cookies.load(environ["HTTP_COOKIE"])
            if "tale_session_id" in cookies:
                session_id = cookies["tale_session_id"].value
                if session_id:
                    print("EXISTING SESSION ID", session_id)
                    pass  # @todo bind to existing session

        headers = []
        if not session_id:
            # @todo create new session
            session_id = "34324324324234324!!!!"
            print("NEW SESSION")
            cookies["tale_session_id"] = session_id
            cookie = cookies["tale_session_id"]
            cookie["expires"] = "session"
            cookie["path"] = "/tale"
            headers = [("set-cookie", morsel.OutputString()) for morsel in cookies.values()]

        start_response("200 OK", headers)
        return [("session test: " + session_id).encode("ascii")]

    def wsgi_handle_login(self, environ, parameters, start_response):
        start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        resource = vfs.internal_resources["web/login.html"]
        message = ""
        txt = resource.data.format(story_name=self.driver.config.name,
                                   message=message)
        return [txt.encode("utf-8")]


class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class CustomWsgiServer(WSGIServer):
    request_queue_size = 200
