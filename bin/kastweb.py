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
MODULE_KASTWEBP = None
IS_QUITING = False


from signal import signal, SIGINT, SIGHUP, SIGTERM, SIGQUIT
def signal_handler(signal_received, frame):
    global IS_QUITING
    if IS_QUITING:return
    IS_QUITING = True
    import os
    import psutil

    MODULE_KASTWEBP.deleteWebFacades()

    if MODULE_KASTWEBP.IO_LOOP!=None:MODULE_KASTWEBP.IO_LOOP.current().stop()

    parent_pid = os.getpid()
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):  # or parent.children() for recursive=False
        child.kill()
    parent.kill()

    import sys
    sys.stdout = None
    sys.exit(0)


def usage():
    return ''

def main(args):
    self_funct='main'
    import optparse
    global VERBOSE, KASTWEB_TEMP_DIR, MODULE_KASTWEBP
    VERBOSE=None
    from kwadlib import kastmenuxception
    from kwadlib import kastwebs
    from kwadlib import default

    MODULE_KASTWEBP = kastwebs.MODULE_KASTWEBP

    parser = optparse.OptionParser(usage())
    parser.add_option("-v", "--verbose", dest="verbose", type=int, default=0, help="The verbose level a number. e.g.: -v10. (beware >= 200 will cause some raise exceptions not be caught)")
    parser.add_option("-H", "--host", dest="host", help="Listener Host.")
    parser.add_option("-p", "--port", dest="port", help="Listener Port.")

    (options, args) = parser.parse_args(args=args)
    VERBOSE=options.verbose

    if len(args) != 0:raise kastmenuxception.kastmenuSystemException('main', 'main', 'No argument is supported !')
    
    try:
        # call(host=None, temp_dir=None, verbose=0)
        kastwebs.call(host=options.host, port=options.port, temp_dir=default.getTempDir(), verbose=options.verbose)

    except Exception as e:

        if VERBOSE==None:
            try:VERBOSE=int(options.verbose)
            except:VERBOSE=0
        if VERBOSE>200:raise

        import sys
        if not hasattr(e, 'short1') or not hasattr(e, 'short2'):
            message=e.__class__.__name__ + ': ' + str(e)
        elif VERBOSE<=100:
            message=e.short1()
        elif VERBOSE>100:
            message=e.short2()
        sys.stderr.write(message + '\n')
        sys.exit(2)


if __name__ == '__main__':
    from os import path
    import utils
    import sys

    signal(SIGINT, signal_handler)
    signal(SIGHUP, signal_handler)
    signal(SIGTERM, signal_handler)
    signal(SIGQUIT, signal_handler)

    INSTALL_DIR = utils.getInstallDir()

    ## Set paths
    for _path in ('core',):
        _path=path.normpath(INSTALL_DIR + '/' + _path)
        if not _path in sys.path:sys.path.append(_path)

    main(sys.argv[1:])