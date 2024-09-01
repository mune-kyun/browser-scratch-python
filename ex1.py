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

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

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

            if self.scheme == URLScheme.DATA:
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

    def request(self):
        if self.is_malformed:
            return self.request_malformed()

        if self.scheme == URLScheme.HTTP or self.scheme == URLScheme.HTTPS:
            return self.request_http()
        elif self.scheme == URLScheme.FILE:
            return self.request_file()
        elif self.scheme == URLScheme.DATA:
            return self.request_data()
        
def lex(resp, mode="lex"):
    ret = []
    buffer = ""
    scheme = resp["scheme"]
    body = resp["content"]
    is_view_source = resp.get("is_view_source", None)
    
    # parse tag
    if scheme in {URLScheme.HTTP, URLScheme.HTTPS}:
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
                    ret.append(Tag(buffer))
                    buffer = ""
                else:
                    buffer += c
            if in_tag:
                buffer = "<" + buffer
            if len(buffer) > 0:
                ret.append(Text(buffer))

    elif scheme == URLScheme.FILE:
        for file in body:
            ret.append(file)

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

    # load(URL(sys.argv[1]))

    elapsed_time_ms, _ = elapsed_ms(load, URL(sys.argv[1]))
    print("elapsed: {} ms".format(elapsed_time_ms))
