from include.numeric_responses import *
from config import config


def welcome(actor):
    ret = [RPL_WELCOME(actor),
           RPL_YOURHOST(actor),
           RPL_CREATED(actor),
           RPL_MOTDSTART(actor)]
    try:
        with open(config.get('server', 'motd_file'), 'r') as f:
            ret += [RPL_MOTD(actor, line.strip()) for line in f]
    except IOError:
        pass
    ret.append(RPL_ENDOFMOTD(actor))
    return ret
