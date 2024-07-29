#!/bin/bash
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


set -x # DEBUG Only
set -e # Fail at first Error.
# Eventually remove temp_dir at EXIT:
## TODO: trap "rm -fr ${TEMP_DIR}" EXIT



# ========================================================================================================= #
# GLOBAL VARIABLES                                                                                          #
# ========================================================================================================= #

## kastagent-install.sh VERSION KAST_AGENT_DIR KAST_WEB_HOST KAST_WEB_PORT
## kastagent-install.sh 1.5 /tmp blabla.com 1234

# Temp dir:
TEMP_DIR=$(eval echo ~${USER})/kastagent_inst
# Backup dir:
BACKUP_DIR=${TEMP_DIR}/backup
# Script dir:
SCRIPT_NAME=kastagent_install.sh
SCRIPT_DIR=$(dirname $0)
if [ "${SCRIPT_DIR}" = '.' ];
then
	SCRIPT_DIR=$PWD;
fi
KAST_INSTALL_DIR=${SCRIPT_DIR:0:-4}
echo "KAST_INSTALL_DIR is: ${KAST_INSTALL_DIR}"



# VERSION:
# --------
VERSION=$1
if test "${VERSION}" == ""
then
echo "Error: Parameter 1: VERSION cannot not be null !"
exit 1
fi
echo "VERSION is: ${VERSION}"


# KAST_AGENT_DIR:
# ---------------
KAST_AGENT_DIR=$2
if test "${KAST_AGENT_DIR}" == ""
then
echo "Error: Parameter 2: KAST_AGENT_DIR cannot not be null !"
exit 1
fi
echo "KAST_AGENT_DIR is: ${KAST_AGENT_DIR}"

# Check Install Dir:
# ------------------
EXCPECTED_BIN_DIR=${KAST_AGENT_DIR}/kastagent/kastagent-${VERSION}
LINK_DIR=${KAST_AGENT_DIR}/kastagent
if test "${KAST_INSTALL_DIR}" != "${EXCPECTED_BIN_DIR}"
then
echo "Error: Real Install directory: ${KAST_INSTALL_DIR} is not equal to the Expected binary directory: ${EXCPECTED_BIN_DIR} guessed from the Version(${VERSION}) !"
exit 1
fi

# KAST_WEB_HOST:
# --------------
KAST_WEB_HOST=$3
if test "${KAST_WEB_HOST}" == ""
then
echo "Error: Parameter 3: KAST_WEB_HOST cannot not be null !"
exit 1
fi
echo "KAST_WEB_HOST is: ${KAST_WEB_HOST}"

# KAST_WEB_PORT:
# --------------
KAST_WEB_PORT=$4
if test "${KAST_WEB_PORT}" == ""
then
echo "Error: Parameter 4: KAST_WEB_PORT cannot not be null !"
exit 1
fi
echo "KAST_WEB_PORT is: ${KAST_WEB_PORT}"

echo "checking Opening on Host(${KAST_WEB_HOST}):Port(${KAST_WEB_PORT}) ..."
cat <<EOF | python3
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('${KAST_WEB_HOST}', ${KAST_WEB_PORT}))
    s.listen(1)
except:
    raise Exception("Failed trying to Open Host(${KAST_WEB_HOST}):Port(${KAST_WEB_PORT}) ! This Host(${KAST_WEB_HOST}) may not be an actual local interface, or Port(${KAST_WEB_PORT}) may be in use ! Advice: if not root user port should be greater than 1024.")
EOF
echo "... checking Opening on Host(${KAST_WEB_PORT}):Port(${KAST_WEB_PORT}) done"


# ========================================================================================================= #
# GLOBAL                                                                                                    #
# ========================================================================================================= #
echo "GLOBAL"
echo "------"


# 1) TEMP DIRS:
# =============
echo "global.1) ReCreates Temporary kastagent dir at: ${TEMP_DIR}:"
# Temp dir:
rm -fr ${TEMP_DIR}
mkdir ${TEMP_DIR}
chmod o-rwx ${TEMP_DIR}
# Backup dir:
mkdir ${BACKUP_DIR}
mkdir ${BACKUP_DIR}/etc
chmod o-rwx ${BACKUP_DIR}


# 2) LINK Current:
# ================
if [ ! -d "${LINK_DIR}/current" ]
then
cd $LINK_DIR
ln -s $KAST_INSTALL_DIR current
fi



# 3) PYTHON Settup:
# =================
echo "global.3) Python Setup at /opt/kastagent/bin/.venv:"
rm -fr ${KAST_INSTALL_DIR}/bin/.venv > /dev/null 2>&1 || echo '' > /dev/null 2>&1
python3 -m venv ${KAST_INSTALL_DIR}/bin/.venv
${KAST_INSTALL_DIR}/bin/.venv/bin/pip3 install -r ${KAST_INSTALL_DIR}/bin/requirements.txt




# 5) GENERATE KAST CONF:
# ======================
echo "global.5) 
a) Generates kastagent conf file at: ${KAST_INSTALL_DIR}/conf/kast.conf."

# ${KAST_INSTALL_DIR}/conf/kast.conf:
# ===================================
install_type=base
cat  <<EOF > ${KAST_INSTALL_DIR}/conf/kast.conf
# Where is kastagent installed this cannot be changed:
install_dir=${KAST_INSTALL_DIR}
verbose=0

# KastMenu Process maximum wait for termination:
process_timeout = 150


#---------------#
# frontend port |
#---------------#
# host: fqdn or ip to join this machine through the network (must not be localhost)
kastweb_host=${KAST_WEB_HOST}
kastweb_port=${KAST_WEB_PORT}


#--------------------#
# kdealer port_range |
#--------------------#
# kdealer port : kdealer is used by apimenu to dispatch menu input/outputs either
# a) from a menu process to another independent menu process but called with --follow_mnu.
# b) to the web via the front kastagent webserver.
kdealer_port_range = [10000,10200]


#--------------#
# Certificates |
#--------------#
# kastweb keys:
# -------------
# Those key will be auto-generated by kastweb at this place,
# (using kastagent with a kastagent-server) at first launch if not exist.
# They will be encrypted.
# But as any user can launch kastweb they must be read accessable to others.
# default: keys/kastweb/kastweb.kastagent.myhostname.crt
kastweb_server_crt = keys/kastweb/kastweb.kastagent.${KAST_WEB_HOST}.crt
# default: keys/kastweb/kastweb.kastagent.myhostname.key
kastweb_server_key = keys/kastweb/kastweb.kastagent.${KAST_WEB_HOST}.key
# default: keys/kastweb/caclients
kastweb_caclients = keys/kastweb/caclients

# kastagent keys:
# ---------------
kastagent_server_crt = keys/kastagent/kastagent.crt
kastagent_server_key = keys/kastagent/kastagent.key
kastagent_caclients = keys/kastagent/caclients


#-------------------------#
# Custom Alias (Optional) |
#-------------------------#
# Alias declared here are available as alias to SoftClasses, Exits and to all the commands.
alias_myvar1 = value1
alias_myvar2 = value2
EOF

# kast.desc.conf:
# =================
echo "global.4) 
b) Generates kast desc file at: ${KAST_INSTALL_DIR}/conf/descs/kast.desc.conf."

cat  <<EOF > ${KAST_INSTALL_DIR}/conf/descs/kast.desc.conf
# Where is kastagent installed this cannot be changed:
install_dir={*required:True,*type:str,*value:${KAST_INSTALL_DIR}}
verbose={*required:True,*type:int,*value:0}

# KastMenu Process maximum wait for termination:
process_timeout={*required:True,*value:300}


#---------#
# Kastweb |
#---------#
# host: fqdn or ip to join this machine through the network (must not be localhost)
kastweb_host={*required:True}
kastweb_port={*type:int}


#--------------#
# kdealer port |
#--------------#
# kdealer port : kdealer is used by apimenu to dispatch menu input/outputs either
# a) from a menu process to another independent menu process but called with --follow_mnu.
# b) to the web via the front kast webserver.
kdealer_port_range = {*type:list,*ltype:{*type:int},*len:2}


#--------------#
# Certificates |
#--------------#
# kastweb keys:
# -------------
# sys rigths on these files must be own=kastagent:kastagent mod=660 or 600
kastweb_server_crt = {*required:True}
kastweb_server_key = {*required:True}
kastweb_caclients = {*required:True}
# Those key will be auto-generated by kastweb in this place,
# (using kastagent with a kastagent-server) at first launch if not exist.
# They will be encrypted.
# But as any user can launch kastweb they must be read accessable to others.

# kastagent keys:
# ---------------
kastagent_server_crt = {*required:True,*value:keys/kastagent/kastagent.crt}
kastagent_server_key = {*required:True,*value:keys/kastagent/kastagent.key}
kastagent_caclients = {*required:True,*value:keys/kastagent/caclients}


#-------------------------#
# Custom Alias (Optional) |
#-------------------------#
# Alias declared here are available as alias to SoftClasses, Exits and to all the commands.
alias_myvar1 = {*type:str}
alias_myvar2 = {*type:str}
EOF


#--------------#
# SSL Generate |
#--------------#
echo "global.5) Generates SSL keys ${KAST_INSTALL_DIR}/conf/keys:"
export KAST_DIR=${KAST_INSTALL_DIR}
export TEMP_DIR=${TEMP_DIR}
${KAST_INSTALL_DIR}/bin/genkastwebkeys

chmod o+rx ${KAST_INSTALL_DIR}/conf/keys

if [ -d /etc/kastmenu/keys/caclients/to_kastweb ] ; then
    cp -r /etc/kastmenu/keys/caclients/to_kastweb/.  ${KAST_INSTALL_DIR}/conf/keys/kastweb/caclients
    chmod o+r ${KAST_INSTALL_DIR}/conf/keys/kastweb/caclients/*.crt
fi


exit 0
