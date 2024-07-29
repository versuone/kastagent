## Copyright (c) 2007-2024, Patrick Germain Placidoux
## All rights reserved.
##
## This file is part of KastMenu (Unixes Operating System's Menus Broadkasting).
##
## KastMenu is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## KastMenu is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with KastMenu.  If not, see <http://www.gnu.org/licenses/>.
##
## Home: http://www.kastmenu.org
## Contact: kastmenu@kastmenu.org


# 001: 2023/09/05 : Replacing JQuery bu Bootsrap5
# Html5 Fetch is far slower then JQuery Ajax, so we can no more loop on get.
# oo WebSocket is renamed oo_websocket_get
# menu_websocket_get is Added to replace all get()

"""
# 20230905: 001: Replacing JQuery bu Bootsrap5
# Html5 Fetch is far slower then JQuery Ajax, so we can no more loop on get.
# oo WebSocket is renamed OOWebSocketGet
# MenuWebSocketGet is Added to replace all get()
"""

import tornado.web
import tornado.websocket
import tornado.gen


IO_LOOP = None
CONNECTION_TIMEOUT=7
VERBOSE = 0

def printlog(fromf, message, level=0):
    from kwadlib.tools import printlog as plog
    plog(fromf, message, level=level, verbose=VERBOSE)

class KastException(tornado.web.HTTPError):

    def __init__(self, status_code=0, log_message=None, reason=None, do_page=False,
        *args,
        **kwargs
    ):
        self.og_reason = reason
        self.do_page = do_page

        # reason: do not support \n => would cause content-length error !
        if reason!=None:reason = reason.replace('\n', '<br>')
        tornado.web.HTTPError.__init__(self, *args, status_code=status_code, log_message=log_message, reason=reason, do_page=do_page, **kwargs)


class BaseHandler():
    __SSLClientCtx =None

    async def prepare(self):
        self.query_arguments = {k:self.request.query_arguments[k][0] for k in self.request.query_arguments}
        for k in self.query_arguments:
            if self.query_arguments[k] == '':self.query_arguments[k] = None

        self.port = self.query_arguments['port'].decode("utf-8")
        self.shasecid = self.query_arguments['shasecid'].decode("utf-8")

    def getKastAgentPort(self):
        return self.port
    def getShasecid(self):
        return self.shasecid

    @staticmethod
    def getSSLClientCtx():
        if BaseHandler.__SSLClientCtx!=None:return BaseHandler.__SSLClientCtx
        from kwadlib import default

        # kastweb_server_crt:
        kastweb_server_crt = default.getKastConfs()['kastweb_server_crt']
        if not kastweb_server_crt.startswith('/'): kastweb_server_crt = default.KAST_CONF_DIR + '/' + kastweb_server_crt
        # kastweb_server_key:
        kastweb_server_key = default.getKastConfs()['kastweb_server_key']
        if not kastweb_server_key.startswith('/'): kastweb_server_key = default.KAST_CONF_DIR + '/' + kastweb_server_key

        # Ssl Management:
        # ---------------
        import ssl
        # See: https://www.tornadoweb.org/en/stable/httpserver.html
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile=kastweb_server_crt, keyfile=kastweb_server_key, password=getPasswordLocal())
        ssl_ctx.check_hostname = False

        BaseHandler.__SSLClientCtx = ssl_ctx

        return BaseHandler.__SSLClientCtx



# ------------------------------------------------------------------------------------------------------ #
# PROXIES:                                                                                               #
# ------------------------------------------------------------------------------------------------------ #

class WebMenuProxyHandler(tornado.web.RequestHandler, BaseHandler):

    async def prepare(self):
        await BaseHandler.prepare(self)

    async def get(self):
        # See: https://www.tornadoweb.org/en/stable/httpclient.html
        from tornado.httpclient import AsyncHTTPClient
        http_client = AsyncHTTPClient()
        try:
            """
            http_client = httpclient.AsyncHTTPClient() 
            http_client.fetch(url, method='POST', body=urllib.parse.urlencode(data))
            """

            # Removing parasite headers from browser:
            headers = self.request.headers
            url = 'https://%s:%s' % ('localhost', self.getKastAgentPort()) + self.request.uri + '?shasecid=%s' % self.getShasecid()
            printlog('WebMenuProxyHandler:', 'Opening WebMenuProxyHandler on this backend url: %s ...' % (url,), level=100)
            response = await http_client.fetch(url, connect_timeout=CONNECTION_TIMEOUT, request_timeout=120,
                headers=headers, follow_redirects=False,

                ssl_options= self.getSSLClientCtx())
        except Exception as e:
            m="Error: %s" % e
            raise KastException(500, reason=m, log_message=m, do_page=True)

        keys = list(response.headers.keys())
        for header in keys:self.set_header(header, response.headers[header])

        self.write(response.body)


class OOWebMenuProxyWebSocketGet(tornado.websocket.WebSocketHandler, BaseHandler):

    async def prepare(self):
        await BaseHandler.prepare(self)

    async def open(self):
        from tornado.websocket import websocket_connect
        from tornado.httpclient import HTTPRequest

        # Open:
        # -----
        url = 'wss://%s:%s/kmenu/oo_websocket_get' % ('localhost', self.getKastAgentPort()) + '?shasecid=%s' %self.getShasecid()
        printlog('OOWebMenuProxyWebSocketGet:', 'Opening WebMenu Output WebSocket on this backend url: %s ...' % (url,), level=100)
        wss_req = HTTPRequest(url,
            validate_cert=False, ssl_options=self.getSSLClientCtx())

        # ws = await websocket_connect(wss_req) support of: connect_timeout:
        import asyncio
        ws = await asyncio.wait_for(websocket_connect(wss_req), timeout=CONNECTION_TIMEOUT)

        ws.on_message = self.on_message
        ws.on_close = self.on_close

        printlog("Main", "OOMenuWebSocket opened")

    def on_message(self, message):
        try:self.write_message(message.replace('<', '&lt;').replace('>', '&gt;'))
        except:
            self.close()

    def on_close(self):
        self.close()

class MenuWebMenuProxyWebSocketGet(tornado.websocket.WebSocketHandler, BaseHandler):

    async def prepare(self):
        await BaseHandler.prepare(self)

    async def open(self):
        from tornado.websocket import websocket_connect
        from tornado.httpclient import HTTPRequest

        # Open:
        # -----
        url = 'wss://%s:%s/kmenu/menu_websocket_get' % ('localhost', self.getKastAgentPort()) + '?shasecid=%s' % self.getShasecid()
        printlog('MenuWebMenuProxyWebSocketGet:', 'Opening WebMenu WebSocket on this backend url: %s ...' % (url,), level=100)
        wss_req = HTTPRequest(url,
            validate_cert=False, ssl_options=self.getSSLClientCtx())

        # ws = await websocket_connect(wss_req) support of: connect_timeout:
        import asyncio
        ws = await asyncio.wait_for(websocket_connect(wss_req), timeout=CONNECTION_TIMEOUT)

        ws.on_message = self.on_message
        ws.on_close = self.on_close

        printlog("Main", "MenuWebSocket opened")


    def on_message(self, message):
        try:self.write_message(message)
        except:
            self.close()

    def on_close(self):
        self.close()


# ------------------------------------------------------------------------------------------------------ #
# UTIL:                                                                                                  #
# ------------------------------------------------------------------------------------------------------ #


def genKastwebKeys(fqdn=None, force=False):
    """
    This will generate kastweb ssl keys:
    ------------------------------------
    """
    self_funct='genKastwebKeys'
    from kwadlib.tools import Popen, SUBPROCESS_STDOUT, SUBPROCESS_PIPE
    from kwadlib.security.crypting import sanitize_hostorip
    from kwadlib import default
    from os import path, remove
    import re

    # kastweb_keys:
    etc_kastweb_keys = path.split(default.getKastConfs()['kastweb_server_crt'])[-2]
    if not etc_kastweb_keys.startswith('/'):etc_kastweb_keys = default.KAST_CONF_DIR + '/' + etc_kastweb_keys
    # kastagent_keys:
    etc_kastagent_keys = path.split(default.getKastConfs()['kastagent_server_crt'])[-2]
    if not etc_kastagent_keys.startswith('/'):etc_kastagent_keys = default.KAST_CONF_DIR + '/' + etc_kastagent_keys
    
    temp_dir = default.getUserKastTempDir()
    passfile = temp_dir + '/fpass.txt'

    envs = {
        'ETC_KASTWEB_KEYS': etc_kastweb_keys,
        'ETC_KASTAGENT_KEYS': etc_kastagent_keys,
        'KAST_DIR': default.getInstallDir(),
        'PASSWORD': getPasswordLocal(),
        'TEMP_DIR': temp_dir
    }

    kastweb_host = default.getKastConfs()['kastweb_host']
    if fqdn!=None:
        if not force and kastweb_host==fqdn:
            print (self_funct + ' New fqdn == previous kastweb_host: %s into %s, nothing to do ! Use force to overpass.' % (kastweb_host, default.KAST_CONF_DIR))
            return
        sanitize_hostorip(do_hide=False, class_exit='Main', method_exit=self_funct, **{'fqdn': fqdn})
        kastweb_host_new = fqdn
        envs['FULL_FRONT_HOSTNAME'] = fqdn
    else:
        import socket
        kastweb_host_new = socket.gethostname()

    with open(passfile, 'w') as f:
        f.write(getPasswordLocal())

    cmd = default.getInstallDir() + '/core/kwadlib/security/sslkeygen/sslkeygen_kastweb.sh'
    try:
        p = Popen(cmd, stdout=SUBPROCESS_PIPE, stderr=SUBPROCESS_STDOUT, executable='/bin/bash', universal_newlines=True, shell=True, env=envs)
        output, errmsg = p.communicate()
        ret = p.wait()
    except:
        raise
    finally:
        if path.isfile(passfile): remove(passfile)

    print (output)

    if p.returncode != 0:
        more=''
        if len(output)!=0: more = ' SubException is: %s' % output
        raise Exception ('Unable to run command: %s !%s' % (cmd, more))

    # Rename:  kastweb.kastmenu.myhostname.key, kastweb.kastmenu.myhostname.crt to real name:
    with open(default.KAST_CONF) as fread:
        src = fread.read()
        # kastweb_host:
        src = re.sub(r"kastweb_host\s*=\s*.*", 'kastweb_host = ' + kastweb_host_new, src)
        # kastweb_server_key:
        src = re.sub(r"kastweb_server_key\s*=\s*.*", 'kastweb_server_key = ' + etc_kastweb_keys + '/' + kastweb_host_new + '.key', src)
        # kastweb_server_crt:
        src = re.sub(r"kastweb_server_crt\s*=\s*.*", 'kastweb_server_crt = ' + etc_kastweb_keys + '/' + kastweb_host_new + '.crt', src)

        with open(default.KAST_CONF, 'w') as fwrite:
            fwrite.write(src)

def killPid(pid):
    # This will kill local bash and childs:
    import psutil

    parent_pid = pid
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):  # or parent.children() for recursive=False
        child.kill()
    parent.kill()
    parent.wait()


def getPasswordLocal():
    from kwadlib.security.crypting import sha256
    from os import path, chmod
    from kwadlib import default
    uuid = None

    # Create uuid file if not E:
    etc_kastweb_keys = path.split(default.getKastConfs()['kastweb_server_crt'])[-2]
    if not etc_kastweb_keys.startswith('/'):etc_kastweb_keys = default.KAST_CONF_DIR + '/' + etc_kastweb_keys
    uuid_path = etc_kastweb_keys + '/uuid.dat'
    if not path.isfile(uuid_path):
        dir = path.split(uuid_path)[0]
        if not path.isdir(dir):
            from os import makedirs
            makedirs(dir)

        from kwadlib.tools import genUid
        uuid=genUid()
        with open(uuid_path, 'w') as f:f.write(uuid)
        chmod(uuid_path, 0o400)
    else:
        with open(uuid_path) as f:
            uuid=f.read()

    return sha256('17380277749631' + str(uuid))
