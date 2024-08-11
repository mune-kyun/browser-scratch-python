import os
import socket
import ssl

class URLScheme:
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"
    DATA = "data"

class URL:
    def __init__(self, url: str):
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

    def request_http(self):
        # create socket
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

        # assert to exclude headers
        assert "transfer-encoding" not in res_headers
        assert "content-encoding" not in res_headers

        # read content(body) and return
        content = res.read()
        s.close()
        return {
            "content": content,
            "scheme": self.scheme
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

    def request(self):
        if self.scheme == URLScheme.HTTP or self.scheme == URLScheme.HTTPS:
            return self.request_http()
        elif self.scheme == URLScheme.FILE:
            return self.request_file()
        elif self.scheme == URLScheme.DATA:
            return self.request_data()
        
def show(resp):
    scheme = resp["scheme"]
    body = resp["content"]
    
    # parse tag
    if scheme in {URLScheme.HTTP, URLScheme.HTTPS}:
        in_tag = False
        for c in body:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                print(c, end="")

    elif scheme == URLScheme.FILE:
        for file in body:
            print(file)

    elif scheme == URLScheme.DATA:
        print(body)

    else:
        print(scheme)
    
def load(url: URL):
    resp = url.request()
    show(resp)

if __name__ == "__main__":
    import sys

    load(URL(sys.argv[1]))
