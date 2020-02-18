# https://github.com/andrewmk/untplib

import time
import ssl
import socket
import json



# public APIs
APIS = {
    'ip': 'https://api.ipify.org?format=json',
    'currentDateTime': 'http://worldclockapi.com/api/json/cet/now'
}



def http_get(url, data=''):
    try:
        prot, _, host, path = url.split('/', 3)
    except:
        prot, _, host = url.split('/', 2)   
        host, path = host.split('?', 1)
        path = '?'+path

    port = 443 if prot == 'https:' else 80
    addr = socket.getaddrinfo(host, port)[0][-1]

    ipv = socket.AF_INET6 if len(addr) == 4 else socket.AF_INET
    s = socket.socket(ipv)
    if prot == 'https:': s = ssl.wrap_socket(s)

    s.connect(addr)
    req = bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n%s' % (path, host, data), 'utf8')
    #print('sending\n-------------------------------\n{}\n-------------------------------'.format(req))
    s.send(req)
    response = b''
    while True:
        chars = s.recv(1000)
        if chars:
            response += chars
        else:
            break
    s.close()
    return str(response, 'utf8')



def http2json( http_response ):
    start = http_response.find('\r\n\r\n') + 4  # match 2 newlines
    return json.loads(http_response[start:])




# extract content after the http header
def http_data(response):
    start = response.find('\r\n\r\n') + 4  # match 2 newlines
    return str(response[start:])








def call_api( key ):
    msg = http_get( APIS[key] )
    status, data = parse_http_response(msg)
    return json.loads(data) if status == '200' else None

def get_time():
    return call_api('currentDateTime')['currentDateTime']


def get_ip():
    ipjson = call_api('ip')
    return ipjson['ip']


# not working, maybe requires cookies?
def get_weather(location = 'munich'):   
    if location != 'munich':
        api = 'https://www.metaweather.com/api/location/search/?query={}'.format(location) # 676757
        msg = http_get( api )
        status, data = parse_http_response(msg)
        woeid = json.loads(data)['woeid']
    else:
        woeid = 676757
    api = 'https://www.metaweather.com/api/location/{}/'.format(woeid) # 676757
    print(api)
    msg = http_get( api )
    print(msg)
    status, data = parse_http_response(msg)
    print(data)
    tempjson = json.loads(data)
    print(tempjson)
    temp = tempjson['consolidated_weather'][0]['the_temp']
    print(temp)





def parse_http_response( msg ):
    first_line = msg.split('\n', 1)[0]
    status = first_line.split(' ', 2)[1]  # E.g. 'HTTP/1.1 404 Not Found'
    start = msg.find('\r\n\r\n') + 4  # match 2 newlines
    data = str(msg[start:])
    if status != '200': print('HTTP Warn: status {}:\n{}'.format(status, data))
    return (status, data)


def parse_http_request( msg ):
    try:
        fields = msg.split('\n', 1)[0].split(' ', 2)
        return (fields[0], fields[1])
    except:
        return (400, '')

def parse_uri( uri ):
    path = uri.split('?')[0]





# WEB-Server
HEADER_OK = 'HTTP/1.1 200 OK\r\nContent-Type: {}\r\n\r\n'
HTML = """<!DOCTYPE html>\n<html>
        <head><title>{}</title> </head>
        <body><h1>{}</h1>{}
        </body>
</html>"""



def nano_handler( path ):
    html = HTML
    json = '{{ "temperature": {} }}'
    if path == b'/test':
        response = bytes( HEADER_OK.format('text/html') + html.format('Test', 'Test Successfull!', ''), 'utf-8' )
        print('test requested!')
    elif path == b'/temperature':
        response = bytes( HEADER_OK.format('application/json') + json.format('23.3'), 'utf-8' )
    else:
        response = b'HTTP/1.1 404 Not Found\r\n\r\n'+bytes( html.format('Not Found', 'Doh! 404', 'Not found.'), 'utf-8' )
    return response




def run_nano_server( path_handler = nano_handler ):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)  # accept max 1 connections

    print('NanoServer listening on {}:{}'.format(addr[0], addr[1]))

    while True:
        client_s, addr = s.accept()
        print('client connected from', addr)
        req = client_s.recv(4096)
        req_fields = req.split(b' ', 2)
        #print(req_fields)
        response = b'HTTP/1.1 404 Not Found\r\n\r\n'+bytes( HTML.format('Not Found', 'Doh!', ''), 'utf-8' )
        if req_fields[0] == b'GET':
            path = req_fields[1]
            print('path: {}'.format(path))
            response = path_handler(path)

        client_s.send(response)
        client_s.close()


#ret = call_api( 'ip' )
#print(ret)


#get_ip()
#run_nano_server()
#get_weather('london')
