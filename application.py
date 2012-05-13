# -*- coding: utf-8 -*-

import gevent.server
import gevent.monkey
gevent.monkey.patch_all()

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

server = gevent.server.StreamServer(('127.0.0.1', 6667), handle)
server.serve_forever()