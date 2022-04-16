import os
import socket
from mimetypes import guess_type
from typing import List, Union

QUEUE_NUM = 5
PORT = 8080
BUF_SIZE = 4096
DATA_DIR = "./data"


class Status:
    OK = "200 OK"
    NOTFOUND = "404 Not Found"
    INTERNALERROR = "504 Internal Error"


class ContentType:
    TEXT = "text/plain"
    # HTML = "text/html"
    # JPEG = "image/jpeg"
    # PNG = "image/png"
    # mimetypesに判定させてそのまま使うことにした


class Request:
    method: str = ""
    path: str = ""
    version: str = ""
    headers: List[str] = []
    body: List[str] = []


def parse_request(request_bytes: bytes) -> Request:
    request = Request()
    request_str = request_bytes.decode("utf-8").split("\r\n")
    request.method, request.path, request.version = request_str[0].split()

    for line in request_str[1:]:
        request.headers.append(line)
        if line == "":
            break
    # NOTE: GET以外に対応するならBODYを取る

    return request


def create_response(request: Request):
    if request.path == "/ping":
        return create_response_bytes(Status.OK, ContentType.TEXT, b"pong")

    else:
        path = DATA_DIR + request.path
        if os.path.isfile(path):
            mimetype, _ = guess_type(path)

            with open(path, "rb") as f:
                body = f.read()
            return create_response_bytes(Status.OK, mimetype, body)

        else:
            return create_response_bytes(Status.NOTFOUND, None, b"")


def create_response_bytes(
    status: str, content_type: Union[str, None], body: bytes
) -> bytes:

    if content_type:
        content_type_text = "Content-Type: " + content_type + "\r\n"
    else:
        content_type_text = ""

    header = f"""\
HTTP/1.1 {status}
{content_type_text}\

\
"""

    _bytes = header.encode("utf-8") + body

    return _bytes


def serve():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", PORT))
        s.listen(QUEUE_NUM)

        (sock, addr) = s.accept()
        print("Connected by" + str(addr))

        with sock:
            try:
                request = sock.recv(BUF_SIZE)
                if not request:
                    print("EMPTY REQUEST")
                    return
                req = parse_request(request)

                res = create_response(req)

                sock.send(res)
            except Exception:
                sock.send(
                    create_response_bytes(Status.INTERNALERROR, "", "").encode("utf-8")
                )


if __name__ == "__main__":
    while True:
        serve()
