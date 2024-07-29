#!/usr/bin/python3
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



##########
## Main ##
##########

SELF_MODULE = 'kastweb'
INSTALL_DIR = None
KASTWEB_TEMP_DIR = None
IS_QUITING = False

from kwadlib import kastwebp
MODULE_KASTWEBP = kastwebp

def call(host=None, port=None, temp_dir=None, verbose=0):
    self_funct='main'
    from kwadlib.security.crypting import sanitize_hostorip
    from kwadlib import kastmenuxception
    from kwadlib import default
    from os import path
    global VERBOSE, KASTWEB_TEMP_DIR
    VERBOSE=None

    # kastweb_server_crt:
    KASTWEB_SERVER_CRT = default.getKastConfs()['kastweb_server_crt']
    if not KASTWEB_SERVER_CRT.startswith('/'):KASTWEB_SERVER_CRT = default.KAST_CONF_DIR + '/' + KASTWEB_SERVER_CRT
    # kastweb_server_key:
    KASTWEB_SERVER_KEY = default.getKastConfs()['kastweb_server_key']
    if not KASTWEB_SERVER_KEY.startswith('/'):KASTWEB_SERVER_KEY = default.KAST_CONF_DIR + '/' + KASTWEB_SERVER_KEY
    # kastweb_caclients:
    KASTWEB_CLIENTS_CACLIENTS = default.getKastConfs()['kastweb_caclients']

    if not KASTWEB_CLIENTS_CACLIENTS.startswith('/'):KASTWEB_CLIENTS_CACLIENTS = default.KAST_CONF_DIR + '/' + KASTWEB_CLIENTS_CACLIENTS

    from kwadlib.tools import RedirectStd
    import sys, datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    RedirectStd(stdout=sys.stdout, stderr=sys.stderr, nostdout=False, nostderr=False, log_dir=default.getKastTempDir(), log_file='kastmenu-%s.log' % ts)
    VERBOSE=verbose
    MODULE_KASTWEBP.VERBOSE = VERBOSE

    import tornado.ioloop, tornado.web
    from os import path, makedirs
    from kwadlib import tools

    kast_attrs = tools.getKastConfs()

    ## aliases:
    aliases = dict(kast_attrs)

    ## Retreives temp_dir:
    if temp_dir != None:KASTWEB_TEMP_DIR = temp_dir
    else:
        current_user = default.getUser()
        if current_user == 'root':home = '/root'
        else:home = '/home/' + current_user
        KASTWEB_TEMP_DIR = '/%s/.kastmenu/temp/' % home + tools.genUid()
        if not path.isdir(KASTWEB_TEMP_DIR):makedirs(KASTWEB_TEMP_DIR)

    tools.verbose(SELF_MODULE + ': kastweb Temporary dir is: ' + KASTWEB_TEMP_DIR + '.', level=VERBOSE, ifLevel=50, indent='', logFile=VERBOSE)

    # Local KManager:
    # ---------------
    # a) Ssl Management:
    import ssl
    # See: https://www.tornadoweb.org/en/stable/httpserver.html
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile=KASTWEB_SERVER_CRT, keyfile=KASTWEB_SERVER_KEY, password=MODULE_KASTWEBP.getPasswordLocal())

    ssl_ctx.load_verify_locations(capath=KASTWEB_CLIENTS_CACLIENTS)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED

    settings = {}
    # http://127.0.0.1:8888/webmenu/webmenu.html
    application = tornado.web.Application([
        (r"/kmenu/do_menu", MODULE_KASTWEBP.WebMenuProxyHandler),
        (r"/kmenu/oo_websocket_get", MODULE_KASTWEBP.OOWebMenuProxyWebSocketGet),
        (r"/kmenu/menu_websocket_get", MODULE_KASTWEBP.MenuWebMenuProxyWebSocketGet)
    ], **settings)

    from os import getpid
    sanitize_hostorip(do_hide=False, class_exit='Main', method_exit=self_funct, **{'host': host})



    # The following two lines are Expected by kastserver:
    print("""Launched Kastweb on host/port {host}:{port} with pid: {pid}
{{"host":"{host}","port":{port},"pid":{pid}}}
Kastweb Launched finished.""".format(host=host, port=port, pid=getpid()))

    http_server = application.listen(port, address=host, ssl_options=ssl_ctx)
    MODULE_KASTWEBP.IO_LOOP = tornado.ioloop.IOLoop.current()
    MODULE_KASTWEBP.IO_LOOP.start()
