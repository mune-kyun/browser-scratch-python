import socket
import ssl

class URL:
    def __init__(self, url: str):
        # split url with scheme (http & example.org)
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

        # separate host and path (example.org and /index)
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # get specified port
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            port = int(port)

    def request(self):
        # create socket
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )

        # pick port
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # connect
        s.connect((self.host, self.port))

        # handle https
        if self.scheme == "https":
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
        return content

def show(body):
    # parse tag
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")
    
def load(url: URL):
    body = url.request()
    show(body)

if __name__ == "__main__":
    import sys

    load(URL(sys.argv[1]))
