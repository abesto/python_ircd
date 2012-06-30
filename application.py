# -*- coding: utf-8 -*-

from config import config

import logging
log = logging.getLogger()

import gevent
import gevent.server
import gevent.monkey
gevent.monkey.patch_all()

from include.dispatcher import Dispatcher
from include.message import Message
from include.router import Router

from models import Actor
dispatcher = Dispatcher()
router = Router(gevent.socket.SHUT_RDWR)

def handle(socket, address):
    fileobj = socket.makefile('rw')
    while not Actor.by_socket(socket).disconnected:
        line = fileobj.readline()
        try:
            msg = Message.from_string(line)
            resp = dispatcher.dispatch(socket, msg)
            router.send(resp)
        except Exception, e:
            log.exception(e)

host = config.get('server', 'listen_host')
port = config.getint('server', 'listen_port')
log.info('Starting server, listening on %s:%s' % (host, port))
server = gevent.server.StreamServer((host, port), handle)
server.serve_forever()
log.info('Server stopped')
