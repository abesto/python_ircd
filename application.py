# -*- coding: utf-8 -*-

from config import config

import logging
log = logging.getLogger()

import gevent
import gevent.server
import gevent.monkey
gevent.monkey.patch_all()

from dispatcher import Dispatcher
dispatcher = Dispatcher()

import message
import router

def handle(socket, address):
    fileobj = socket.makefile('rw')
    disconnect = False
    while not disconnect:
        line = fileobj.readline()
        try:
            msg = message.from_string(line)
            resp = dispatcher.dispatch(socket, msg)
            if resp is None:
                continue
            if type(resp) is not list:
                resp = [resp]
            if 'disconnect' in resp:
                resp.remove('disconnect')
                disconnect = True
            router.send(resp)
        except Exception, e:
            log.exception(e)
    try:
        socket.shutdown(gevent.socket.SHUT_RDWR)
    except:
        pass
    socket.close()

host = config.get('server', 'listen_host')
port = config.getint('server', 'listen_port')
log.info('Starting server, listening on %s:%s' % (host, port))
server = gevent.server.StreamServer((host, port), handle)
server.serve_forever()
log.info('Server stopped')
