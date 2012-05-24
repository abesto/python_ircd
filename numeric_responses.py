import config
from message import Message

def M(*args, **kwargs):
    kwargs['add_nick'] = True
    return Message(*args, **kwargs)

def RPL_WELCOME(user):
    return M(user, '001', 'Welcome to the Internet Relay Network %s' % str(user))
def RPL_YOURHOST(user):
    return M(user, '002', 'Your host is %s running an experimental server' % config.servername)
def RPL_CREATED(user):
    return M(user, '003', 'This server was created %s' % config.created)

def RPL_WHOREPLY(target, user, mask):
    # H = Here
    # G = Away
    # * = IRCOp
    # @ = Channel Op
    # + = Voiced
    return M(target, '352', mask, user.username, user.hostname, config.servername, user.nickname,
        # TODO: more flags, if needed
        'G' if user.away else 'H', '0 ' + user.realname
    )
def RPL_ENDOFWHO(target, mask):
    return M(target, '315', mask, 'End of WHO list')

def RPL_NOTOPIC(target, channel):
    return M(target, '331', str(channel), 'No topic is set')
def RPL_TOPIC(target, channel, **kwargs):
    return M(target, '332', str(channel), channel.topic, **kwargs)

def RPL_NAMEREPLY(user, channel):
    # TODO: choose prefix based on channel mode
    prefix = '='
    # TODO: add user prefix if needed
    nicks = ' '.join(channel_user.nickname for channel_user in channel.users)
    return M(user, '353', prefix, str(channel), nicks)
def RPL_ENDOFNAMES(user):
    return M(user, '366', 'End of NAMES list')

def RPL_MOTDSTART(user):
    return M(user, '375', '- %s Message of the day - ' % config.servername)
def RPL_MOTD(user, text):
    return M(user, '372', '- %s' % text)
def RPL_ENDOFMOTD(user):
    return M(user, '376', 'End of MOTD command')

def ERR_NOSUCHNICK(nickname, user):
    return M(user, '401', nickname, 'No such nick/channel')
def ERR_NOSUCHCHANNEL(channel_name, user):
    return M(user, '401', channel_name, 'No such channel')


def ERR_NOSUCHSERVER(server, target):
    return M(target, '402', server, 'No such server')
def ERR_CANNOTSENDTOCHAN(channelname, target):
    return M(target, '404', channelname, 'Cannot send to channel')
def ERR_NORECIPIENT(command, target):
    return M(target, '411', 'No recipient given ' + command)
def ERR_NOTEXTTOSEND(target):
    return M(target, '412', 'No text to send')
def ERR_NONICKNAMEGIVEN(target):
    return M(target, '431', 'No nickname given')
def ERR_ERRONEUSNICKNAME(nickname, target):
    return M(target, '432', nickname, 'Erroneous nickname')
def ERR_NICKNAMEINUSE(nickname, target):
    return M(target, '433', nickname, 'Nickname is already in use')
def ERR_NICKCOLLISION(nickname, target):
    return M(target, '436', nickname, 'Nickname collision KILL')
def ERR_NOTREGISTERED(target):
    return M(target, '451', 'You have not registered')
def ERR_NEEDMOREPARAMS(command, target):
    return M(target, '461', command, 'Not enough parameters')
def ERR_ALREADYREGISTRED(target):
    return M(target, '462', 'You may not reregister')
