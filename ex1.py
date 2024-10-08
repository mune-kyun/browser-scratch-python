import os
import socket
import ssl

from util import elapsed_ms

class URLScheme:
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"
    DATA = "data"
    VIEW_SOURCE = "view-source"
    TEST = "test"

class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent
    
    def __repr__(self):
        return repr(self.text)

class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes
    
    def __repr__(self):
        return "<" + self.tag + ">"

class HTMLParser:
    SELF_CLOSING_TAGS = [
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    ]
    HEAD_TAGS = [
        "base", "basefont", "bgsound", "noscript",
        "link", "meta", "title", "style", "script",
    ]

    def __init__(self, body):
        self.body = body
        self.unfinished = []

    # Process body per character
    def parse(self):
        buffer = ""
        in_tag = False

        for c in self.body:
            # append normal text before meeting start tag
            if c == "<":
                in_tag = True
                if buffer: self.add_text(buffer)
                buffer = ""
            # end of tag, then append
            elif c == ">":
                in_tag = False
                self.add_tag(buffer)
                buffer = ""
            else:
                buffer += c

        if in_tag:
            buffer = "<" + buffer
            self.add_text(buffer)
        
        return self.finish()
    
    # Process text type node
    def add_text(self, text):
        if len(self.unfinished) < 1: return
        if text.isspace(): return

        self.implicit_tags(None) # guard to add missing body, head, or mandatory tags

        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    # Process html tag type node
    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        
        if tag.startswith("!"): return # skip !doctype
        if tag.isspace(): return # skip \n or whitespace after doctype
        
        self.implicit_tags(tag) # guard to add missing body, head, or mandatory tags

        if tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        elif tag.startswith("/"):
            if len(self.unfinished) == 1: return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    # Extract attributes from it's tag
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}

        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.casefold()] = value
            else:
                attributes[attrpair.casefold()] = ""

        return tag, attributes

    # Add missing mandatory tags such as html, head, body
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]

            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] \
                and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] \
                and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break

    # Make sure that only one parent node is returned
    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)

        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)

        return self.unfinished.pop()

def print_tree(node, indent=0):
    print(" " * indent, node)
    if isinstance(node, Element): print(" " * indent, f"({node.attributes})")
    for child in node.children:
        print_tree(child, indent + 2)

class URL:
    def __init__(self, url: str):
        self.is_malformed = False
        self.extract_url(url)

    def extract_url(self, url):
        try:
            # view source mode
            self.is_view_source = URLScheme.VIEW_SOURCE in url
            if self.is_view_source is True:
                _, url = url.split(":", 1)

            # split url with scheme (http & example.org)
            if URLScheme.HTTP in url:
                self.scheme = URLScheme.HTTP
                sep = "://"
            elif URLScheme.HTTPS in url:
                self.scheme = URLScheme.HTTPS
                sep = "://"
            elif URLScheme.FILE in url:
                self.scheme = URLScheme.FILE
                sep = ":///"
            elif URLScheme.DATA in url:
                self.scheme = URLScheme.DATA
                sep = ","
            elif URLScheme.TEST in url:
                self.scheme = URLScheme.TEST
                sep = ","

            if self.scheme == URLScheme.DATA:
                _, url = url.split(sep, 1)
            elif self.scheme == URLScheme.TEST:
                _, url = url.split(sep, 1)
            else:
                self.scheme, url = url.split(sep, 1)

            # separate host and path (example.org and /index)
            if self.scheme in {URLScheme.HTTP, URLScheme.HTTPS}:
                if "/" not in url:
                    url = url + "/"
                self.host, url = url.split("/", 1)
                self.path = "/" + url

                # get specified port
                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    port = int(port)

            elif self.scheme == URLScheme.FILE:
                self.path = url

            elif self.scheme == URLScheme.DATA:
                self.content = url

            elif self.scheme == URLScheme.TEST:
                self.content = url
        
        except Exception as e:
            print(f"Extract URL error: {e}")
            self.is_malformed = True

    def request_http(self):
        # create socket
        s = None
        res = ""
        while True:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP
            )
            # pick port
            if self.scheme == URLScheme.HTTP:
                self.port = 80
            elif self.scheme == URLScheme.HTTPS:
                self.port = 443

            # connect
            s.connect((self.host, self.port))

            # handle https
            if self.scheme == URLScheme.HTTPS:
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            # form request
            req = "GET {} HTTP/1.0\r\n".format(self.path)
            req += "Host: {}\r\n".format(self.host)
            req += "Connection: {}\r\n".format("close")
            req += "User-Agent: {}\r\n".format("mozilla")
            req += "\r\n"
            s.send(req.encode("utf-8"))

            # get response
            res = s.makefile("r", encoding="utf-8", newline="\r\n")

            # split response
            statusline = res.readline()
            version, status, explanation = statusline.split(" ", 2)
            res_headers = {}
            while True:
                line = res.readline()
                if line == "\r\n": break
                header, value = line.split(":", 1)
                res_headers[header.casefold()] = value.strip()

            if "location" in res_headers:
                s.close()
                self.extract_url(res_headers["location"])
            else:
                break

        # assert to exclude headers
        assert "transfer-encoding" not in res_headers
        assert "content-encoding" not in res_headers

        # read content(body) and return
        content = res.read()
        s.close()
        return {
            "content": content,
            "scheme": self.scheme,
            "is_view_source": self.is_view_source
        }

    def request_file(self):
        file_list = []
        files = os.listdir(self.path)
        for file in files:
            file_list.append(file)
        
        return {
            "content": file_list,
            "scheme": self.scheme
        }
    
    def request_data(self):
        return {
            "content": self.content,
            "scheme": self.scheme
        }
    
    def request_malformed(self):
        return {
            "content": "",
            "scheme": "malformed"
        }

    def request_test(self):
        return {
            "content": self.content,
            "scheme": self.scheme
        }

    def request(self):
        if self.is_malformed:
            return self.request_malformed()

        if self.scheme == URLScheme.HTTP or self.scheme == URLScheme.HTTPS:
            return self.request_http()
        elif self.scheme == URLScheme.FILE:
            return self.request_file()
        elif self.scheme == URLScheme.DATA:
            return self.request_data()
        elif self.scheme == URLScheme.TEST:
            return self.request_test()
        
# TODO: move completely to build tree
# Get Text, Element from a body / Normal parsing
def lex(resp, mode="lex"):
    ret = []
    buffer = ""
    scheme = resp["scheme"]
    body = resp["content"]
    is_view_source = resp.get("is_view_source", None)
    
    # parse tag
    if scheme in {URLScheme.HTTP, URLScheme.HTTPS, URLScheme.TEST}:
        if is_view_source:
            ret.append(body)
        else:
            in_tag = False
            for c in body:
                # append normal text before meeting start tag
                if c == "<":
                    in_tag = True
                    if len(buffer) > 0:
                        ret.append(Text(buffer))
                    buffer = ""
                # end of tag, then append
                elif c == ">":
                    in_tag = False
                    ret.append(Element(buffer))
                    buffer = ""
                else:
                    buffer += c
            if in_tag:
                buffer = "<" + buffer
            if len(buffer) > 0:
                ret.append(Text(buffer))

    elif scheme == URLScheme.FILE:
        for file in body:
            ret.append(Text(file))
            ret.append(Text("\n"))

    elif scheme == URLScheme.DATA:
        ret.append(body)

    else:
        ret.append(body)

    if mode == "lex":
        return ret
    else:
        print(ret)
    
def load(url: URL):
    resp = url.request()
    lex(resp, mode="show")

if __name__ == "__main__":
    import sys

    url = sys.argv[1]
    body = URL(url).request()
    nodes = HTMLParser(body["content"]).parse()
    print_tree(nodes)
