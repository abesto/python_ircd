# -*- coding: utf-8 -*-

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
    while True:
        line = fileobj.readline()
        print 'In:  %s -> %s' % (repr(socket.client), repr(line))
        try:
            msg = message.from_string(line)
        except message.Error, e:
            print e.message
        else:
            resp = dispatcher.dispatch(socket, msg)
            print 'Out: %s' % repr(resp)
            router.send(resp)
            try:
                if 'disconnect' in resp:
                    socket.close()
                    return
            except TypeError:
                pass

server = gevent.server.StreamServer((config.listen_host, config.listen_port), handle)
server.serve_forever()