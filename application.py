# -*- coding: utf-8 -*-

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
        print 'In:  %s -> %s' % (repr(socket.client), repr(line))
        try:
            msg = message.from_string(line)
        except message.Error, e:
            print e.message
        else:
            resp = dispatcher.dispatch(socket, msg)
            if resp is None:
                continue
            if type(resp) is not list:
                resp = [resp]
            print 'Out: %s' % repr(resp)
            if 'disconnect' in resp:
                resp.remove('disconnect')
                disconnect = True
            router.send(resp)
    try:
        socket.shutdown(gevent.socket.SHUT_RDWR)
    except:
        pass
    socket.close()

server = gevent.server.StreamServer((config.listen_host, config.listen_port), handle)
server.serve_forever()
