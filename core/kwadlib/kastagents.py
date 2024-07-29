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

SELF_MODULE = 'kastagents'
INSTALL_DIR = None
KASTAGENT_TEMP_DIR = None
IS_QUITING = False

from kwadlib import kastagentp
MODULE_KASTAGENTP = kastagentp

def call(menufile, host=None, debug=None, record=None, show=None, log=None, log_dir=None, log_rotate=None, log_output=None, show_shortcut=None, batch=None, go=None, go_menu=None, pause=None, tmpl_kws=None, temp_dir=None, keep_temp_dir=False, verbose=0):
    self_funct='main'
    from kwadlib.security.crypting import sanitize_hostorip
    from kwadlib import kastmenuxception
    from kwadlib import default
    from os import path
    global VERBOSE, KASTAGENT_TEMP_DIR
    VERBOSE=None

    # kastagent_server_crt:
    KASTAGENT_SERVER_CRT = default.getKastConfs()['kastagent_server_crt']
    if not KASTAGENT_SERVER_CRT.startswith('/'):KASTAGENT_SERVER_CRT = default.KAST_CONF_DIR + '/' + KASTAGENT_SERVER_CRT
    # kastagent_server_key:
    KASTAGENT_SERVER_KEY = default.getKastConfs()['kastagent_server_key']
    if not KASTAGENT_SERVER_KEY.startswith('/'):KASTAGENT_SERVER_KEY = default.KAST_CONF_DIR + '/' + KASTAGENT_SERVER_KEY
    # kastagent_caclients:
    KASTAGENT_CLIENTS_CACLIENTS = default.getKastConfs()['kastagent_caclients']
    if not KASTAGENT_CLIENTS_CACLIENTS.startswith('/'):KASTAGENT_CLIENTS_CACLIENTS = default.KAST_CONF_DIR + '/' + KASTAGENT_CLIENTS_CACLIENTS

    from kwadlib.tools import RedirectStd
    import sys, datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    RedirectStd(stdout=sys.stdout, stderr=sys.stderr, nostdout=False, nostderr=False, log_dir=default.getKastTempDir(), log_file='kastmenu-%s.log' % ts)
    VERBOSE=verbose


    if not path.isfile(menufile): raise kastmenuxception.kastmenuSystemException('main', 'main', 'File: %s should Exist !' % menufile)

    import tornado.ioloop, tornado.web
    from os import path, makedirs
    from kwadlib import tools

    kast_attrs = tools.getKastConfs()

    ## aliases:
    aliases = dict(kast_attrs)

    ## Retreives temp_dir:
    if temp_dir != None:KASTAGENT_TEMP_DIR = temp_dir
    else:
        current_user = default.getUser()
        if current_user == 'root':home = '/root'
        else:home = '/home/' + current_user
        KASTAGENT_TEMP_DIR = '/%s/.kastmenu/temp/' % home + tools.genUid()
        if not path.isdir(KASTAGENT_TEMP_DIR):makedirs(KASTAGENT_TEMP_DIR)

    tools.verbose(SELF_MODULE + ': kastagent Temporary dir is: ' + KASTAGENT_TEMP_DIR + '.', level=VERBOSE, ifLevel=50, indent='', logFile=VERBOSE)

    MODULE_KASTAGENTP.initWebFacade(menufile, is_listening=True, show_shortcut=show_shortcut,
        log=log, log_output=log_output, log_dir=log_dir, log_rotate=log_rotate,
        temp_dir = KASTAGENT_TEMP_DIR, keep_temp_dir = keep_temp_dir,
        aliases=aliases, tmpl_kws=tmpl_kws,
        record = record, show=show, batch = batch, go = go, go_menu = go_menu, pause = pause, debug = debug, verbose = verbose)
    MODULE_KASTAGENTP.startWebFacade()

    HOST = 'localhost'
    PORT = MODULE_KASTAGENTP.MENU_WEB_FACADE.getPort()
    TEMP_DIR = MODULE_KASTAGENTP.MENU_WEB_FACADE.getTempDir()
    SHASECID = MODULE_KASTAGENTP.MENU_WEB_FACADE.getShaSecid()


    # Local KManager:
    # ---------------
    # a) Ssl Management:
    import ssl
    # See: https://www.tornadoweb.org/en/stable/httpserver.html
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile=KASTAGENT_SERVER_CRT, keyfile=KASTAGENT_SERVER_KEY, password=None)

    ssl_ctx.load_verify_locations(capath=KASTAGENT_CLIENTS_CACLIENTS)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED

    settings = {}
    # http://127.0.0.1:8888/webmenu/webmenu.html
    application = tornado.web.Application([
        (r"/kmenu/do_menu", MODULE_KASTAGENTP.MainPageHandler),
        (r"/kmenu/oo_websocket_get", MODULE_KASTAGENTP.OOWebSocketGet),
        (r"/kmenu/menu_websocket_get", MODULE_KASTAGENTP.MenuWebSocketGet)
    ], **settings)

    from os import getpid
    if host != None:
        sanitize_hostorip(do_hide=False, class_exit='Main', method_exit=self_funct, **{'host': host})
        host = host
    else:host = HOST

    if host == 'localhost': # if host is localhost grab a new port not to conflict with the kdealer port:
        PORT = default.getFreePortOnLocalHost()

    # The following two lines are Expected by kastserver:
    print("""Launching Kastagent on host/port {host}:{port} with pid: {pid}
{{"host":"{host}","port":{port},"pid":{pid},"shasecid":"{shasecid}", "temp_dir": "{temp_dir}"}}
Kastagent Launched finished.""".format(host=host, port=PORT, pid=getpid(), shasecid=SHASECID, temp_dir=TEMP_DIR))

    http_server = application.listen(PORT, address=host, ssl_options=ssl_ctx)
    MODULE_KASTAGENTP.IO_LOOP = tornado.ioloop.IOLoop.current()
    MODULE_KASTAGENTP.IO_LOOP.start()
