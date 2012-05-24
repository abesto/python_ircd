from numeric_responses import *

def welcome(user):
    f = open(config.motd_file, 'r')
    ret =  [RPL_WELCOME(user),
            RPL_YOURHOST(user),
            RPL_CREATED(user),
            RPL_MOTDSTART(user)]
    ret += [RPL_MOTD(user, line.strip()) for line in f]
    f.close()
    ret.append(RPL_ENDOFMOTD(user))
    return ret

