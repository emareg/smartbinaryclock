
import socket

import sys
MICROPYTHON = True if sys.implementation.name == 'micropython' else False
if MICROPYTHON:
    import _thread
else:
    import threading


# WEB-Server
HEADER_OK = 'HTTP/1.1 200 OK\r\nContent-Type: {}\r\n\r\n'
HTML = """<!DOCTYPE html>\n<html>
        <head><title>{title}</title> </head>
        <body><h1>{title}</h1>
        <p>{content}</p>
        </body>
</html>"""

HTML_404 = b'HTTP/1.1 404 Not Found\r\n\r\n'+bytes( HTML.format(title='Not Found', content=''), 'utf-8' )



def nano_handler( path ):
    html = HTML
    json = '{{ "temperature": {} }}'
    if path == b'/' or path == b'/index.html':
        response = load_html()
    elif path == b'/test':
        response = bytes( HEADER_OK.format('text/html') + html.format(title='Test Succ', content=''), 'utf-8' )
        print('test requested!')
    elif path == b'/temperature':
        response = bytes( HEADER_OK.format('application/json') + json.format('23.3'), 'utf-8' )
    else:
        print('path: {}'.format(path))
        response = b'HTTP/1.1 404 Not Found\r\n\r\n'+bytes( html.format(title='Not Found', content='We are sorry.'), 'utf-8' )
    return response


def load_html( path='/index.html' ):
    f = open('.'+path, 'r')
    html = f.read()
    response = bytes( HEADER_OK.format('text/html') + html, 'utf-8' )
    f.close()
    return response




def parse_location( string ):
    pass



def serve_forever( path_handler = nano_handler ):
    if MICROPYTHON:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        #addr = socket.getaddrinfo(socket.gethostname(), 8080, socket.AF_INET6)[0][-1]
    else:
        #addr = socket.getaddrinfo('::1', 8080)[0][-1]
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        addr = socket.getaddrinfo(socket.gethostname(), 8080, socket.AF_INET6)[0][-1]  #[0:2]
        addr = ('::1', 8080)   # ports above 1024 require root

    print(addr)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(1)  # accept max 1 connections

    print('NanoServer listening on {}:{}'.format(addr[0], addr[1]))

    while True:
        client_s, addr = s.accept()
        print('client connected from', addr)
        req = client_s.recv(4096)
        req_fields = req.split(b' ', 2)
        #print(req_fields)
        response = HTML_404
        if req_fields[0] == b'GET':
            path = req_fields[1]
            print('path: {}'.format(path))
            response = path_handler(path)

        if not isinstance(response, bytes):
            response = HTML_404
        client_s.send(response)
        client_s.close()



def dummy_handler( req ):
    return bytes( HEADER_OK.format('text/html') + HTML.format(title='Nano Server Default', content='no handler defined'), 'utf-8')



# provides a thread for nano server
class WebSrv:

    def __init__(self, request_handler = dummy_handler):
        self.request_handler = request_handler
        #super(WebSrv, self).__init__()

    def run(self):
        serve_forever( self.request_handler )


    def start(self):
        if MICROPYTHON:
            _thread.start_new_thread(serve_forever, (self.request_handler, ))
        else:
            self.run()


def test():
    srv = WebSrv(nano_handler)
    srv.start()

# test()
