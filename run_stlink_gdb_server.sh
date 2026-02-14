#!/bin/bash

echo "run_stlink_gdb_server.sh started with arguments:"

export GDB_PORT=$1
echo "  GDB_PORT: ${GDB_PORT}"

export GDB_SWO_PORT=$2
echo "  GDB_SWO_PORT: ${GDB_SWO_PORT}"

export GDB_SERVER_PATH=$3
echo "  GDB_SERVER_PATH: ${GDB_SERVER_PATH}"

export STLINK_PROG_DIR=$4
echo "  STLINK_PROG_DIR: ${STLINK_PROG_DIR}"

export APID=$5
echo "  APID: ${APID}"

${GDB_SERVER_PATH} \
--port-number ${GDB_PORT} \
--swd \
--shared \
--swo-port ${GDB_SWO_PORT} \
--attach \
--verbose \
-cp ${STLINK_PROG_DIR} \
-m ${APID}
