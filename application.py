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
        except Exception, e:
            log.exception(e)
            actor = Actor.by_socket(socket)
            if actor.is_user() and actor.get_user().registered.nick and actor.get_user().registered.user:
                resp = [
                    Message(actor, 'NOTICE', 'The message your client has just sent could not be parsed. If you think'),
                    Message(actor, 'NOTICE', 'this is a problem with the server, please open an issue at:'),
                    Message(actor, 'NOTICE', 'https://github.com/abesto/python-ircd'),
                    Message(actor, 'NOTICE', '---'),
                    Message(actor, 'NOTICE', 'The message sent by your client was:'),
                    Message(actor, 'NOTICE', line.strip("\n")),
                    Message(actor, 'NOTICE', '---'),
                    Message(actor, 'NOTICE', 'Closing connection.')
                ]
                quit_resp = dispatcher.dispatch(socket, Message(None, 'QUIT', 'Invalid message'))
                if isinstance(quit_resp, list):
                    resp += quit_resp
                else:
                    resp.append(quit_resp)
            else:
                resp = Message(actor, 'ERROR')
            Actor.by_socket(socket).disconnect()
        else:
            resp = dispatcher.dispatch(socket, msg)

        try:
            router.send(resp)
        except Exception, e:
            log.exception(e)
            Actor.by_socket(socket).disconnect()

host = config.get('server', 'listen_host')
port = config.getint('server', 'listen_port')
log.info('Starting server, listening on %s:%s' % (host, port))
server = gevent.server.StreamServer((host, port), handle)
server.serve_forever()
log.info('Server stopped')
