# coding=utf-8
"""
Webbrowser based I/O for a single player ('if') story.

'Tale' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
from __future__ import absolute_import, print_function, division
from wsgiref.simple_server import make_server
import cgi
import json
from email.utils import formatdate, parsedate
from . import iobase
from . import vfs
from .. import mud_context
try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape


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
    "monospaced": "{{pre}}",
    "/monospaced": "{{/pre}}"
}
escaped_styles_to_html = {
    "{{pre}}": "<pre>",
    "{{/pre}}": "</pre>"
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
        import webbrowser
        from threading import Thread
        url = "http://%s:%d/tale/" % self.server.server_address
        t = Thread(target=webbrowser.open, args=(url, ))
        t.start()
        while not self.stop_main_loop:
            self.server.handle_request()

    def pause(self, unpause=False):
        pass   # @todo

    def install_tab_completion(self, completer):
        self.completer = completer

    def render_output(self, paragraphs, **params):
        for text, formatted in paragraphs:
            text = self._convert_to_html(text)
            if text == "\n":
                text = "<br>"
            if formatted:
                self.text_to_browser.append("<p>" + text + "</p>\n")
            else:
                self.text_to_browser.append("<pre>" + text + "</pre>\n")

    def output(self, *lines):
        for line in lines:
            self.output_no_newline(line)

    def output_no_newline(self, text):
        text = self._convert_to_html(text)
        if text == "\n":
            text = "<br>"
        self.text_to_browser.append("<p>" + text + "</p>\n")

    def _convert_to_html(self, line):
        """Convert style tags to html"""
        if "<" not in line:
            return line
        elif style_words:
            for tag, replacement in style_words.items():
                line = line.replace("<%s>" % tag, replacement)
            line = html_escape(line)
            for tag, replacement in escaped_styles_to_html.items():
                line = line.replace(tag, replacement)
            return line
        else:
            return html_escape(iobase.strip_text_styles(line))

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

    def wsgi_redirect_other(self, start_response, target):
        """Called to do a redirect see-other"""
        start_response('303 See Other', [('Location', target)])
        return []

    def wsgi_not_modified(self, start_response):
        """Called to signal that a resource wasn't modified"""
        start_response('304 Not Modified', [])
        return []

    def wsgi_process_request(self, environ, path, parameters, start_response):
        if not path:
            headers = [('Content-Type', 'text/html; charset=utf-8')]
            resource = vfs.internal_resources["web/index.html"]
            etag = str(id(self.player_connection))
            if resource.mtime:
                etag += "-" + str(resource.mtime)
                headers.append(("Last-Modified", formatdate(resource.mtime)))
                if_modified = environ.get('HTTP_IF_MODIFIED_SINCE')
                if if_modified:
                    if parsedate(if_modified) >= parsedate(formatdate(resource.mtime)):
                        # the resource wasn't modified since last requested
                        return self.wsgi_not_modified(start_response)
            if_none = environ.get('HTTP_IF_NONE_MATCH')
            if if_none and (if_none == '*' or etag in if_none):
                return self.wsgi_not_modified(start_response)
            headers.append(("ETag", etag))
            start_response('200 OK', headers)
            txt = resource.data.format(story_version=mud_context.driver.config.version,
                                       story_name=mud_context.driver.config.name,
                                       story_author=mud_context.driver.config.author,
                                       story_author_email=mud_context.driver.config.author_address)
            return [txt.encode("utf-8")]
        if path == "text":
            text = self.text_to_browser
            self.text_to_browser = []
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8'),
                                      ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                      ('Pragma', 'no-cache'),
                                      ('Expires', '0')])
            if "fullpage" not in parameters:
                return (t.encode("utf-8") for t in text)
            else:
                resource = vfs.internal_resources["web/textpage.html"]
                txt = resource.data.format(contents="\n".join(text))
                return [txt.encode("utf-8")]
        elif path == "tabcomplete":
            start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8'),
                                      ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                                      ('Pragma', 'no-cache'),
                                      ('Expires', '0')])
            return [json.dumps(self.completer.complete(parameters["prefix"])).encode("utf-8")]
        elif path == "input":
            cmd = parameters.get("cmd", "")
            if cmd and "autocomplete" in parameters:
                self.text_to_browser.append("Suggestions: " + str(self.completer.complete(cmd)))
            else:
                self.text_to_browser.append("<br><pre>   %s</pre>" % cmd)
                self.player_connection.player.store_input_line(cmd)
            return self.wsgi_redirect_other(start_response, "../tale/")
        elif path.startswith("static/"):
            path = path[len("static/"):]
            if not self.wsgi_is_asset_allowed(path):
                return self.wsgi_not_found(start_response)
            try:
                return self.wsgi_serve_static("web/" + path, environ, start_response)
            except IOError:
                return self.wsgi_not_found(start_response)
        return self.wsgi_not_found(start_response)

    def wsgi_is_asset_allowed(self, path):
        return path.endswith(".html") or path.endswith(".js") or path.endswith(".jpg") \
               or path.endswith(".png") or path.endswith(".gif") or path.endswith(".css") or path.endswith(".ico")

    def wsgi_serve_static(self, path, environ, start_response):
        headers = []
        resource = vfs.internal_resources[path]
        if resource.mtime:
            mtime_formatted = formatdate(resource.mtime)
            etag = str(resource.mtime)
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
