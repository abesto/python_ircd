# -*- coding: utf-8 -*-

import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s\t%(message)s'))
log.addHandler(handler)

import gevent
import gevent.server
import gevent.monkey
gevent.monkey.patch_all()

import config
import dispatcher
import message
import router


def handle(socket, address):
    socket.client = None
    fileobj = socket.makefile('rw')
    disconnect = False
    while not disconnect:
        line = fileobj.readline()
        try:
            msg = message.from_string(line)
            log.debug('<= %s %s (raw: %s)' % (repr(socket.client), repr(msg), repr(line)))
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

log.info('Starting server, listening on %s:%s' % (config.listen_host, config.listen_port))
server = gevent.server.StreamServer((config.listen_host, config.listen_port), handle)
server.serve_forever()
log.info('Server stopped')

