from include.numeric_responses import *
from config import config


def welcome(actor):
    f = open(config.get('server', 'motd_file'), 'r')
    ret = [RPL_WELCOME(actor),
           RPL_YOURHOST(actor),
           RPL_CREATED(actor),
           RPL_MOTDSTART(actor)]
    ret += [RPL_MOTD(actor, line.strip()) for line in f]
    f.close()
    ret.append(RPL_ENDOFMOTD(actor))
    return ret
