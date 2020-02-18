import json
import sys
import ssl
import gevent

if sys.version_info[0] < 3:
    from urlparse import urlparse, urlunparse
else:
    from urllib.parse import urlparse, urlunparse
import websockets
import asyncio
from ._transport import Transport


class WebSocketsTransport(Transport):
    def __init__(self, session, connection):
        Transport.__init__(self, session, connection)
        self.ws = None
        self.__requests = {}

    def _get_name(self):
        return 'webSockets'

    @staticmethod
    def __get_ws_url_from(url):
        parsed = urlparse(url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        url_data = (scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)

        return urlunparse(url_data)

    def start(self):
        ws_url = self.__get_ws_url_from(self._get_url('connect'))

        self._session.get(self._get_url('start'))

        print(ws_url)
        print(self.__get_headers())
#        ssl_context                = ssl.create_default_context()
#        ssl_context.check_hostname = False
#        ssl_context.verify_mode    = ssl.CERT_NONE

        with websockets.connect(ws_url, extra_headers = self.__get_headers()) as self.ws:
#        with websockets.connect(ws_url, ssl=ssl_context, extra_headers = self.__get_headers()) as self.ws:
            def _receive():
                print('ws_transport: receive')
                while(True):
                    notification = self.ws.recv()
                    if notification is not None:
                        print('ws_transport: receive->notification')
                        self._handle_notification(notification)
            return _receive

    def send(self, data):
        self.ws.send(json.dumps(data))
        gevent.sleep()

    def close(self):
        self.ws.close()

    def accept(self, negotiate_data):
        return bool(negotiate_data['TryWebSockets'])

    class HeadersLoader(object):
        def __init__(self, headers):
            self.headers = headers

    def __get_headers(self):
        headers = self._session.headers
        loader = WebSocketsTransport.HeadersLoader(headers)

        if self._session.auth:
            self._session.auth(loader)

        return ['%s: %s' % (name, headers[name]) for name in headers]

    def __get_cookie_str(self):
        return '; '.join([
                             '%s=%s' % (name, value)
                             for name, value in self._session.cookies.items()
                             ])
