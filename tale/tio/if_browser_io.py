# coding=utf-8
"""
Webbrowser based I/O for a single player ('if') story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import json
import time
import sys
from hashlib import md5
from email.utils import formatdate, parsedate
from . import iobase
from . import vfs
from .styleaware_wrapper import tag_split_re
from .. import __version__ as tale_version_str
if sys.version_info < (3, 0):
    from cgi import escape as html_escape
    from urlparse import parse_qs
else:
    from html import escape as html_escape
    from urllib.parse import parse_qs

__all__ = ["HttpIo", "TaleWsgiApp", "TaleWsgiAppBase"]


style_tags_html = {
    "<dim>": ("<span class='txt-dim'>", "</span>"),
    "<normal>": ("<span class='txt-normal'>", "</span>"),
    "<bright>": ("<span class='txt-bright'>", "</span>"),
    "<ul>": ("<span class='txt-ul'>", "</span>"),
    "<it>": ("<span class='txt-it'>", "</span>"),
    "<rev>": ("<span class='txt-rev'>", "</span>"),
    "</>": None,
    "<clear>": None,
    "<living>": ("<span class='txt-living'>", "</span>"),
    "<player>": ("<span class='txt-player'>", "</span>"),
    "<item>": ("<span class='txt-item'>", "</span>"),
    "<exit>": ("<span class='txt-exit'>", "</span>"),
    "<location>": ("<span class='txt-location'>", "</span>"),
    "<monospaced>": ("<span class='txt-monospaced'>", "</span>")
}


def singlyfy_parameters(parameters):
    """
    Makes a cgi-parsed parameter dictionary into a dict where the values that
    are just a list of a single value, are converted to just that single value.
    """
    for key, value in parameters.items():
        if isinstance(value, (list, tuple)) and len(value) == 1:
            parameters[key] = value[0]
    return parameters


# @todo: protect the display and transmission of account/password input text
class HttpIo(iobase.IoAdapterBase):
    """
    I/O adapter for a http/browser based interface.
    This doubles as a wsgi app and runs as a web server using wsgiref.
    This way it is a simple call for the driver, it starts everything that is needed.
    """
    def __init__(self, player_connection, wsgi_server):
        super(HttpIo, self).__init__(player_connection)
        self.wsgi_server = wsgi_server
        self.html_to_browser = []     # the lines that need to be displayed in the player's browser
        self.html_special = []      # special out of band commands (such as 'clear')

    def __repr__(self):
        return "<HttpIo @ 0x%x, port %d>" % (id(self), self.port)

    def singleplayer_mainloop(self, player_connection):
        """mainloop for the web browser interface for single player mode"""
        import webbrowser
        from threading import Thread
        url = "http://%s:%d/tale/" % self.wsgi_server.server_address
        print("\nWeb server url:  ", url, end="\n\n")
        t = Thread(target=webbrowser.open, args=(url, ))
        t.daemon = True
        t.start()
        while not self.stop_main_loop:
            self.wsgi_server.handle_request()
        print("Game shutting down.")

    def pause(self, unpause=False):
        pass

    def clear_screen(self):
        self.html_special.append("clear")

    def render_output(self, paragraphs, **params):
        for text, formatted in paragraphs:
            text = self.convert_to_html(text)
            if text == "\n":
                text = "<br>"
            if formatted:
                self.html_to_browser.append("<p>" + text + "</p>\n")
            else:
                self.html_to_browser.append("<pre>" + text + "</pre>\n")

    def output(self, *lines):
        super(HttpIo, self).output(*lines)
        for line in lines:
            self.output_no_newline(line)

    def output_no_newline(self, text):
        super(HttpIo, self).output_no_newline(text)
        text = self.convert_to_html(text)
        if text == "\n":
            text = "<br>"
        self.html_to_browser.append("<p>" + text + "</p>\n")

    def convert_to_html(self, line):
        """Convert style tags to html"""
        chunks = tag_split_re.split(line)
        if len(chunks) == 1:
            # optimization in case there are no markup tags in the text at all
            return html_escape(self.smartquotes(line), False)
        result = []
        close_tags_stack = []
        chunks.append("</>")   # add a reset-all-styles sentinel
        for chunk in chunks:
            html_tags = style_tags_html.get(chunk)
            if html_tags:
                chunk = html_tags[0]
                close_tags_stack.append(html_tags[1])
            elif chunk == "</>":
                while close_tags_stack:
                    result.append(close_tags_stack.pop())
                continue
            elif chunk == "<clear>":
                self.html_special.append("clear")
            elif chunk:
                if chunk.startswith("</"):
                    chunk = "<" + chunk[2:]
                    html_tags = style_tags_html.get(chunk)
                    if html_tags:
                        chunk = html_tags[1]
                        if close_tags_stack:
                            close_tags_stack.pop()
                else:
                    # normal text (not a tag)
                    chunk = html_escape(self.smartquotes(chunk), False)
            result.append(chunk)
        return "".join(result)


class TaleWsgiAppBase(object):
    """
    Generic wsgi functionality that is not tied to a particular
    single or multiplayer web server.
    """
    def __init__(self, driver):
        self.driver = driver

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD")
        path = environ.get('PATH_INFO', '').lstrip('/')
        if not path:
            return self.wsgi_redirect(start_response, "/tale/")
        if path.startswith("tale/"):
            if method in ("GET", "POST"):
                if method == "POST":
                    clength = int(environ['CONTENT_LENGTH'])
                    if clength > 1e6:
                        raise ValueError('Maximum content length exceeded')
                    inputstream = environ['wsgi.input']
                    qs = inputstream.read(clength)
                    if sys.version_info >= (3, 0):
                        qs = qs.decode("utf-8")
                elif method == "GET":
                    qs = environ.get("QUERY_STRING", "")
                if sys.version_info < (3, 0):
                    parameters = singlyfy_parameters(parse_qs(qs))
                    for key, value in parameters.items():
                        parameters[key] = value.decode("UTF-8")
                else:
                    parameters = singlyfy_parameters(parse_qs(qs, encoding="UTF-8"))
                return self.wsgi_route(environ, path[5:], parameters, start_response)
            else:
                return self.wsgi_invalid_request(start_response)
        return self.wsgi_not_found(start_response)

    def wsgi_route(self, environ, path, parameters, start_response):
        if not path or path == "start":
            return self.wsgi_handle_start(environ, parameters, start_response)
        elif path == "about":
            return self.wsgi_handle_about(environ, parameters, start_response)
        elif path == "story":
            return self.wsgi_handle_story(environ, parameters, start_response)
        elif path == "text":
            return self.wsgi_handle_text(environ, parameters, start_response)
        elif path == "tabcomplete":
            return self.wsgi_handle_tabcomplete(environ, parameters, start_response)
        elif path == "input":
            return self.wsgi_handle_input(environ, parameters, start_response)
        elif path.startswith("static/"):
            return self.wsgi_handle_static(environ, path, start_response)
        elif path == "quit":
            return self.wsgi_handle_quit(environ, parameters, start_response)
        return self.wsgi_not_found(start_response)

    def wsgi_invalid_request(self, start_response):
        """Called if invalid http method."""
        start_response('405 Method Not Allowed', [('Content-Type', 'text/plain')])
        return [b'Error 405: Method Not Allowed']

    def wsgi_not_found(self, start_response):
        """Called if Url not found."""
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'Error 404: Not Found']

    def wsgi_redirect(self, start_response, target):
        """Called to do a redirect"""
        start_response('302 Found', [('Location', target)])
        return []

    def wsgi_redirect_other(self, start_response, target):
        """Called to do a redirect see-other"""
        start_response('303 See Other', [('Location', target)])
        return []

    def wsgi_not_modified(self, start_response):
        """Called to signal that a resource wasn't modified"""
        start_response('304 Not Modified', [])
        return []

    def wsgi_internal_server_error(self, start_response, message=""):
        """Called when an internal server error occurred"""
        start_response('500 Internal server error', [])
        return [message.encode("utf-8")]

    def wsgi_handle_start(self, environ, parameters, start_response):
        # start page / titlepage
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        resource = vfs.internal_resources["web/index.html"]
        etag = self.etag(id(self), time.mktime(self.driver.server_started.timetuple()), resource.mtime, "start")
        if_none = environ.get('HTTP_IF_NONE_MATCH')
        if if_none and (if_none == '*' or etag in if_none):
            return self.wsgi_not_modified(start_response)
        headers.append(("ETag", etag))
        start_response("200 OK", headers)
        txt = resource.data.format(story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   story_author=self.driver.config.author,
                                   story_author_email=self.driver.config.author_address)
        return [txt.encode("utf-8")]

    def wsgi_handle_story(self, environ, parameters, start_response):
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        resource = vfs.internal_resources["web/story.html"]
        etag = self.etag(id(self), time.mktime(self.driver.server_started.timetuple()), resource.mtime, "story")
        if_none = environ.get('HTTP_IF_NONE_MATCH')
        if if_none and (if_none == '*' or etag in if_none):
            return self.wsgi_not_modified(start_response)
        headers.append(("ETag", etag))
        start_response('200 OK', headers)
        txt = resource.data.format(story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   story_author=self.driver.config.author,
                                   story_author_email=self.driver.config.author_address)
        return [txt.encode("utf-8")]

    def wsgi_handle_text(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        conn = session.get("player_connection")
        if not conn:
            return self.wsgi_internal_server_error(start_response, "not logged in")
        html, conn.io.html_to_browser = conn.io.html_to_browser, []
        special, conn.io.html_special = conn.io.html_special, []
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        response = {"text": "\n".join(html)}
        if html and conn.player:
            response["turns"] = conn.player.turns
            response["location"] = conn.player.location.title
            response["special"] = special
        return [json.dumps(response).encode("utf-8")]

    def wsgi_handle_tabcomplete(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        conn = session.get("player_connection")
        if not conn:
            return self.wsgi_internal_server_error(start_response, "not logged in")
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        return [json.dumps(conn.io.tab_complete(parameters["prefix"], self.driver)).encode("utf-8")]

    def wsgi_handle_input(self, environ, parameters, start_response):
        session = environ["wsgi.session"]
        conn = session.get("player_connection")
        if not conn:
            return self.wsgi_internal_server_error(start_response, "not logged in")
        cmd = parameters.get("cmd", "")
        if cmd and "autocomplete" in parameters:
            suggestions = conn.io.tab_complete(cmd, self.driver)
            if suggestions:
                conn.io.html_to_browser.append("<br><p><em>Suggestions:</em></p>")
                conn.io.html_to_browser.append("<p class='txt-monospaced'>" + " &nbsp; ".join(suggestions) + "</p>")
            else:
                conn.io.html_to_browser.append("<p>No matching commands.</p>")
        else:
            cmd = html_escape(cmd, False)
            if cmd:
                if conn.io.dont_echo_next_cmd:
                    conn.io.dont_echo_next_cmd = False
                else:
                    conn.io.html_to_browser.append("<span class='txt-userinput'>%s</span>" % cmd)
            conn.player.store_input_line(cmd)
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return []

    def wsgi_handle_license(self, environ, parameters, start_response):
        license = "The author hasn't provided any license information."
        if self.driver.config.license_file:
            license = self.driver.resources[self.driver.config.license_file].data
        resource = vfs.internal_resources["web/about_license.html"]
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        etag = self.etag(id(self), time.mktime(self.driver.server_started.timetuple()), resource.mtime, "license")
        if_none = environ.get('HTTP_IF_NONE_MATCH')
        if if_none and (if_none == '*' or etag in if_none):
            return self.wsgi_not_modified(start_response)
        headers.append(("ETag", etag))
        start_response("200 OK", headers)
        txt = resource.data.format(license=license,
                                   story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   story_author=self.driver.config.author,
                                   story_author_email=self.driver.config.author_address)
        return [txt.encode("utf-8")]

    def wsgi_handle_static(self, environ, path, start_response):
        path = path[len("static/"):]
        if not self.wsgi_is_asset_allowed(path):
            return self.wsgi_not_found(start_response)
        try:
            return self.wsgi_serve_static("web/" + path, environ, start_response)
        except IOError:
            return self.wsgi_not_found(start_response)

    def wsgi_is_asset_allowed(self, path):
        return path.endswith(".html") or path.endswith(".js") or path.endswith(".jpg") \
            or path.endswith(".png") or path.endswith(".gif") or path.endswith(".css") or path.endswith(".ico")

    def etag(self, *components):
        return '"' + md5("-".join(str(c) for c in components).encode("ascii")).hexdigest() + '"'

    def wsgi_serve_static(self, path, environ, start_response):
        headers = []
        resource = vfs.internal_resources[path]
        if resource.mtime:
            # unfortunately, this is usually only present when running under python 3.x...
            mtime_formatted = formatdate(resource.mtime)
            etag = self.etag(id(vfs.internal_resources), resource.mtime, path)
            if_modified = environ.get('HTTP_IF_MODIFIED_SINCE')
            if if_modified:
                if parsedate(if_modified) >= parsedate(mtime_formatted):
                    # the resource wasn't modified since last requested
                    return self.wsgi_not_modified(start_response)
            if_none = environ.get('HTTP_IF_NONE_MATCH')
            if if_none and (if_none == '*' or etag in if_none):
                return self.wsgi_not_modified(start_response)
            headers.append(("ETag", etag))
            headers.append(("Last-Modified", formatdate(resource.mtime)))
        if type(resource.data) is bytes:
            headers.append(('Content-Type', resource.mimetype))
            data = resource.data
        else:
            headers.append(('Content-Type', resource.mimetype + "; charset=utf-8"))
            data = resource.data.encode("utf-8")
        start_response('200 OK', headers)
        return [data]


class TaleWsgiApp(TaleWsgiAppBase):
    """
    The actual wsgi app that the player's browser connects to.
    Note that it is deliberatly simplistic and ony able to handle a single
    player connection; it only works for 'if' single-player game mode.
    """
    def __init__(self, driver, player_connection):
        super(TaleWsgiApp, self).__init__(driver)
        self.completer = None
        self.player_connection = player_connection   # just a single player here

    @classmethod
    def create_app_server(cls, driver, player_connection):
        wsgi_app = SessionMiddleware(cls(driver, player_connection))
        wsgi_server = make_server(driver.config.mud_host, driver.config.mud_port, app=wsgi_app, handler_class=CustomRequestHandler, server_class=CustomWsgiServer)
        wsgi_server.timeout = 0.5
        return wsgi_server

    def wsgi_handle_quit(self, environ, parameters, start_response):
        # Quit/logged out page. For single player, simply close down the whole driver.
        start_response('200 OK', [('Content-Type', 'text/html')])
        self.driver._stop_driver()
        return [b"<html><body><script>window.close();</script>Session ended. You may close this window/tab.</body></html>"]

    def wsgi_handle_about(self, environ, parameters, start_response):
        # about page
        if "license" in parameters:
            return self.wsgi_handle_license(environ, parameters, start_response)
        start_response("200 OK", [('Content-Type', 'text/html; charset=utf-8')])
        resource = vfs.internal_resources["web/about.html"]
        txt = resource.data.format(tale_version=tale_version_str,
                                   story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   uptime="%d:%02d:%02d" % self.driver.uptime,
                                   starttime=self.driver.server_started)
        return [txt.encode("utf-8")]


class CustomRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class CustomWsgiServer(WSGIServer):
    request_queue_size = 10


class SessionMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["wsgi.session"] = {
            "id": None,
            "player_connection": self.app.player_connection
        }
        return self.app(environ, start_response)
