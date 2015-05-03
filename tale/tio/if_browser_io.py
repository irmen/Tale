# coding=utf-8
"""
Webbrowser based I/O for a single player ('if') story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division, unicode_literals
from wsgiref.simple_server import make_server
import cgi
import json
from . import iobase
from . import vfs
from .. import mud_context

__all__ = ["HttpIo"]


style_words = {
    "dim": "",
    "normal": "",
    "bright": "",
    "ul": "",
    "it": "",
    "rev": "",
    "/": "",
    "blink": "",
    "living": "",
    "player": "",
    "item": "",
    "exit": "",
    "location": "",
    "monospaced": "<pre>",
    "/monospaced": "</pre>"
}
assert len(set(style_words.keys()) ^ iobase.ALL_STYLE_TAGS) == 0, "mismatch in list of style tags"


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
    I/O adapter for a http/browser based interface
    """
    def __init__(self, player_connection):
        super(HttpIo, self).__init__(player_connection)
        self.port = 8080
        self.server = make_server("localhost", self.port, app=self.wsgi_app)
        self.server.timeout = 0.5
        self.completer = None
        self.text_to_browser = []

    def __repr__(self):
        return "<HttpIo @ 0x%x, port %d>" % (id(self), self.port)

    def mainloop(self, player_connection):
        while not self.stop_main_loop:
            self.server.handle_request()

    def pause(self, unpause=False):
        pass   # @todo

    def install_tab_completion(self, completer):
        self.completer = completer

    def render_output(self, paragraphs, **params):
        for text, formatted in paragraphs:
            text = self._apply_style(text).strip()
            if not text:
                continue
            if formatted:
                self.text_to_browser.append("<p>" + text + "</p>\n")
            else:
                self.text_to_browser.append("<pre>" + text + "</pre>\n")

    def output(self, *lines):
        for line in lines:
            self.output_no_newline(line)

    def output_no_newline(self, text):
        text = self._apply_style(text).strip()
        if text:
            self.text_to_browser.append("<p>" + text + "</p>\n")

    def _apply_style(self, line):
        """Convert style tags to html"""
        if "<" not in line:
            return line
        elif style_words:
            for tag in style_words:
                line = line.replace("<%s>" % tag, style_words[tag])
            return line
        else:
            return iobase.strip_text_styles(line)

    def wsgi_app(self, environ, start_response):
        method = environ.get("REQUEST_METHOD")
        path = environ.get('PATH_INFO', '').lstrip('/')
        if not path:
            return self.wsgi_redirect(start_response, "/tale/")
        if path.startswith("tale/"):
            if method in ("GET", "POST"):
                parameters = singlyfy_parameters(cgi.parse(environ['wsgi.input'], environ))
                return self.wsgi_process_request(environ, path[5:], parameters, start_response)
            else:
                return self.wsgi_invalid_request(start_response)
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

    def wsgi_process_request(self, environ, path, parameters, start_response):
        print("REQ", path, parameters)  # XXX
        if not path:
            resource = vfs.internal_resources["web/index.html"]
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            txt = resource.data.format(story_version=mud_context.driver.config.version,
                                       story_name=mud_context.driver.config.name,
                                       story_author=mud_context.driver.config.author,
                                       story_author_email=mud_context.driver.config.author_address)
            return [txt.encode("utf-8")]
        if path == "text":
            text = self.text_to_browser
            self.text_to_browser = []
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            return (t.encode("utf-8") for t in text)
        elif path == "tabcomplete":
            start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')])
            return [json.dumps(self.completer.complete(parameters["prefix"])).encode("utf-8")]
        elif path == "input":
            cmd = parameters.get("cmd", "")
            if cmd and "autocomplete" in parameters:
                self.text_to_browser.append("Suggestions: " + str(self.completer.complete(cmd)))
            else:
                self.player_connection.player.store_input_line(cmd)
            return self.wsgi_redirect(start_response, ".")
        elif path.startswith("static/"):
            path = path[len("static/"):]
            if not self.wsgi_is_asset_allowed(path):
                return self.wsgi_not_found(start_response)
            try:
                return self.wsgi_serve_static("web/" + path, start_response)
            except IOError:
                return self.wsgi_not_found(start_response)
        return self.wsgi_not_found(start_response)

    def wsgi_is_asset_allowed(self, path):
        return path.endswith(".html") or path.endswith(".js") or path.endswith(".jpg") \
               or path.endswith(".png") or path.endswith(".gif") or path.endswith(".css") or path.endswith(".ico")

    def wsgi_serve_static(self, path, start_response):
        resource = vfs.internal_resources[path]
        if type(resource.data) is bytes:
            start_response('200 OK', [('Content-Type', resource.mimetype)])
            return [resource.data]
        start_response('200 OK', [('Content-Type', resource.mimetype + "; charset=utf-8")])
        return [resource.data.encode("utf-8")]
