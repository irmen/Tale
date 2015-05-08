# coding=utf-8
"""
Webbrowser based I/O for a single player ('if') story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import cgi
import json
import time
from hashlib import md5
from email.utils import formatdate, parsedate
from . import iobase
from . import vfs
from .styleaware_wrapper import tag_split_re
from .. import __version__ as tale_version_str
try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape

__all__ = ["HttpIo", "TaleWsgiApp", "TaleWsgiAppBase"]


style_tags_html = {
    "<dim>": ("<span class='txt-dim'>", "</span>"),
    "<normal>": ("<span class='txt-normal'>", "</span>"),
    "<bright>": ("<span class='txt-bright'>", "</span>"),
    "<ul>": ("<span class='txt-ul'>", "</span>"),
    "<it>": ("<span class='txt-it'>", "</span>"),
    "<rev>": ("<span class='txt-rev'>", "</span>"),
    "</>": None,
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


class HttpIo(iobase.IoAdapterBase):
    """
    I/O adapter for a http/browser based interface.
    This doubles as a wsgi app and runs as a web server using wsgiref.
    This way it is a simple call for the driver, it starts everything that is needed.
    """
    def __init__(self, player_connection, wsgi_app, wsgi_server):
        super(HttpIo, self).__init__(player_connection)
        self.wsgi_app = wsgi_app
        self.server = wsgi_server

    def __repr__(self):
        return "<HttpIo @ 0x%x, port %d>" % (id(self), self.port)

    def singleplayer_mainloop(self, player_connection):
        """mainloop for the web browser interface for single player mode"""
        import webbrowser
        from threading import Thread
        url = "http://%s:%d/tale/" % self.server.server_address
        print("\nPoint your browser to the following url: ", url, end="\n\n")
        t = Thread(target=webbrowser.open, args=(url, ))
        t.daemon = True
        t.start()
        while not self.stop_main_loop:
            self.server.handle_request()
        print("Game shutting down.")

    def pause(self, unpause=False):
        pass

    def install_tab_completion(self, completer):
        self.server.completer = completer

    def render_output(self, paragraphs, **params):
        for text, formatted in paragraphs:
            text = self.convert_to_html(text)
            if text == "\n":
                text = "<br>"
            if formatted:
                self.wsgi_app.html_to_browser.append("<p>" + text + "</p>\n")
            else:
                self.wsgi_app.html_to_browser.append("<pre>" + text + "</pre>\n")

    def output(self, *lines):
        for line in lines:
            self.output_no_newline(line)

    def output_no_newline(self, text):
        text = self.convert_to_html(text)
        if text == "\n":
            text = "<br>"
        self.wsgi_app.html_to_browser.append("<p>" + text + "</p>\n")

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
                parameters = singlyfy_parameters(cgi.parse(environ['wsgi.input'], environ))
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

    def wsgi_handle_about(self, environ, parameters, start_response):
        # about page
        start_response("200 OK", [('Content-Type', 'text/html; charset=utf-8')])
        resource = vfs.internal_resources["web/about.html"]
        txt = resource.data.format(tale_version=tale_version_str,
                                   story_version=self.driver.config.version,
                                   story_name=self.driver.config.name,
                                   uptime="%d:%02d:%02d" % self.driver.uptime,
                                   starttime=self.driver.server_started,
                                   num_players=len(self.driver.all_players))
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
        self.html_to_browser = []     # the lines that need to be displayed in the player's browser

    @classmethod
    def create_app_server(cls, driver, player_connection):
        wsgi_app = cls(driver, player_connection)
        wsgi_server = make_server("localhost", 8180, app=wsgi_app, handler_class=CustomRequestHandler, server_class=CustomWsgiServer)
        wsgi_server.timeout = 0.5
        return wsgi_app, wsgi_server

    def wsgi_handle_start(self, environ, parameters, start_response):
        # start page / titlepage
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        etag = self.etag(id(self.player_connection), time.mktime(self.driver.server_started.timetuple()), "start")
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
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        resource = vfs.internal_resources["web/story.html"]
        etag = self.etag(id(self.player_connection), time.mktime(self.driver.server_started.timetuple()), "story")
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
        html, self.html_to_browser = self.html_to_browser, []
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        response = {"text": "\n".join(html)}
        if html and self.player_connection and self.player_connection.player:
            response["turns"] = self.player_connection.player.turns
            response["location"] = self.player_connection.player.location.title
        return [json.dumps(response).encode("utf-8")]

    def wsgi_handle_tabcomplete(self, environ, parameters, start_response):
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                  ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                  ('Pragma', 'no-cache'),
                                  ('Expires', '0')])
        return [json.dumps(self.completer.complete(parameters["prefix"])).encode("utf-8")]

    def wsgi_handle_input(self, environ, parameters, start_response):
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
    request_queue_size = 10
