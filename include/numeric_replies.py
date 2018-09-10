"""
Functions to generate numeric replies defined in
https://tools.ietf.org/html/rfc2812#section-2.4 (Numeric Replies) and
https://tools.ietf.org/html/rfc2812#section-5.1 (Command Responses)
"""
from config import config
from models import User, Channel, Target
from include.message import Message


# pylint: disable=invalid-name


def _M(*args, **kwargs) -> Message:
    """
    Wrapper used by the other functions. `add_nick` is set to true,
    which will add the nickname of `Target` of the `Message` to the serialized
    response. This is usually what we want for direct responses to commands.
    """
    kwargs["add_nick"] = True
    return Message(*args, **kwargs)


def RPL_WELCOME(target: Target) -> Message:
    """
    001    RPL_WELCOME
           "Welcome to the Internet Relay Network
           <nick>!<user>@<host>"
    """
    return _M(
        target,
        "001",
        "Welcome to the Internet Relay Network %s" % str(target.get_user()),
    )


def RPL_YOURHOST(target: Target) -> Message:
    """
    002    RPL_YOURHOST
           "Your host is <servername>, running version <ver>"
    """
    return _M(
        target,
        "002",
        "Your host is %s running an experimental server"
        % config.get("server", "servername"),
    )


def RPL_CREATED(target: Target) -> Message:
    """
    003    RPL_CREATED
           "This server was created <date>"
    """
    return _M(
        target, "003", "This server was created %s" % config.get("server", "created")
    )


def RPL_WHOREPLY(target: Target, user: User, mask: str) -> Message:
    """
    352    RPL_WHOREPLY
              "<channel> <user> <host> <server> <nick>
              ( "H" / "G" > ["*"] [ ( "@" / "+" ) ]
              :<hopcount> <real name>"

      - The RPL_WHOREPLY and RPL_ENDOFWHO pair are used
        to answer a WHO message.  The RPL_WHOREPLY is only
        sent if there is an appropriate match to the WHO
        query.  If there is a list of parameters supplied
        with a WHO message, a RPL_ENDOFWHO MUST be sent
        after processing each list item with <name> being
        the item.
    """
    # H = Here
    # G = Away
    # * = IRCOp
    # @ = Channel Op
    # + = Voiced
    return _M(
        target,
        "352",
        mask,
        user.username,
        user.hostname,
        config.get("server", "servername"),
        user.nickname,
        # TODO: more flags, if needed
        "G" if user.away else "H",
        "0 " + user.realname,
    )


def RPL_ENDOFWHO(target: Target, mask: str) -> Message:
    """
    315    RPL_ENDOFWHO
           "<name> :End of WHO list"
    """
    return _M(target, "315", mask, "End of WHO list")


def RPL_NOTOPIC(target: Target, channel: Channel) -> Message:
    """
    331    RPL_NOTOPIC
           "<channel> :No topic is set"
    """
    return _M(target, "331", str(channel), "No topic is set")


def RPL_TOPIC(target: Target, channel: Channel, **kwargs) -> Message:
    """
    332    RPL_TOPIC
           "<channel> :<topic>"

      - When sending a TOPIC message to determine the
        channel topic, one of two replies is sent.  If
        the topic is set, RPL_TOPIC is sent back else
        RPL_NOTOPIC.
    """
    return _M(target, "332", str(channel), channel.topic, **kwargs)


def RPL_NAMEREPLY(target: Target, channel: Channel) -> Message:
    """
    353    RPL_NAMREPLY
           "( "=" / "*" / "@" ) <channel>
            :[ "@" / "+" ] <nick> *( " " [ "@" / "+" ] <nick> )
      - "@" is used for secret channels, "*" for private
        channels, and "=" for others (public channels).
    """
    # TODO: choose prefix based on channel mode
    prefix = "="
    # TODO: add user prefix if needed
    # TODO: this would probably need to be split into multiple messages if the user list is long
    nicks = " ".join(channel_user.nickname for channel_user in channel.users)
    return _M(target, "353", prefix, str(channel), nicks)


def RPL_ENDOFNAMES(target: Target) -> Message:
    """
    366    RPL_ENDOFNAMES
           "<channel> :End of NAMES list"

      - To reply to a NAMES message, a reply pair consisting
        of RPL_NAMREPLY and RPL_ENDOFNAMES is sent by the
        server back to the client.  If there is no channel
        found as in the query, then only RPL_ENDOFNAMES is
        returned.  The exception to this is when a NAMES
        message is sent with no parameters and all visible
        channels and contents are sent back in a series of
        RPL_NAMEREPLY messages with a RPL_ENDOFNAMES to mark
        the end.
    """
    return _M(target, "366", "End of NAMES list")


def RPL_MOTDSTART(target: Target) -> Message:
    """
    375    RPL_MOTDSTART
                   ":- <server> Message of the day - "
    """
    return _M(
        target, "375", "- %s Message of the day - " % config.get("server", "servername")
    )


def RPL_MOTD(target: Target, text: str) -> Message:
    """
    372     RPL_MOTD
                    ":- <text>"
    """
    return _M(target, "372", "- %s" % text)


def RPL_ENDOFMOTD(target: Target) -> Message:
    """
    376     RPL_ENDOFMOTD
                    ":End of /MOTD command"

            - When responding to the MOTD message and the MOTD file
              is found, the file is displayed line by line, with
              each line no longer than 80 characters, using
              RPL_MOTD format replies.  These should be surrounded
              by a RPL_MOTDSTART (before the RPL_MOTDs) and an
              RPL_ENDOFMOTD (after).
    """
    return _M(target, "376", "End of MOTD command")


def ERR_NOSUCHNICK(nickname: str, target: Target) -> Message:
    """
    401    ERR_NOSUCHNICK
           "<nickname> :No such nick/channel"

       - Used to indicate the nickname parameter supplied to a
         command is currently unused.
    """
    return _M(target, "401", nickname, "No such nick/channel")


def ERR_NOSUCHCHANNEL(channel_name: str, target: Target) -> Message:
    """
    403    ERR_NOSUCHCHANNEL
            "<channel name> :No such channel"

      - Used to indicate the given channel name is invalid.
    """
    return _M(target, "401", channel_name, "No such channel")


def ERR_NOSUCHSERVER(server: str, target: Target) -> Message:
    """
    402    ERR_NOSUCHSERVER
           "<server name> :No such server"

      - Used to indicate the server name given currently
        does not exist.
    """
    return _M(target, "402", server, "No such server")


def ERR_CANNOTSENDTOCHAN(channel_name: str, target: Target) -> Message:
    """
    404    ERR_CANNOTSENDTOCHAN
           "<channel name> :Cannot send to channel"

      - Sent to a user who is either (a) not on a channel
        which is mode +n or (b) not a chanop (or mode +v) on
        a channel which has mode +m set or where the user is
        banned and is trying to send a PRIVMSG message to
        that channel.
    """
    return _M(target, "404", channel_name, "Cannot send to channel")


def ERR_NORECIPIENT(command: str, target: Target) -> Message:
    """
    411    ERR_NORECIPIENT
           ":No recipient given (<command>)"
    """
    return _M(target, "411", "No recipient given " + command)


def ERR_NOTEXTTOSEND(target: Target) -> Message:
    """
    412    ERR_NOTEXTTOSEND
           ":No text to send"
    """
    return _M(target, "412", "No text to send")


def ERR_UNKNOWNCOMMAND(command: str, target: Target):
    return _M(target, "421", "{} :Unknown command".format(command))


def ERR_NONICKNAMEGIVEN(target):
    return _M(target, "431", "No nickname given")


def ERR_ERRONEUSNICKNAME(nickname, target):
    return _M(target, "432", nickname, "Erroneous nickname")


def ERR_NICKNAMEINUSE(nickname, target):
    return _M(target, "433", nickname, "Nickname is already in use")


def ERR_NICKCOLLISION(nickname, target):
    return _M(target, "436", nickname, "Nickname collision KILL")


def ERR_NOTONCHANNEL(channel, target):
    return _M(target, "442", channel, "You're not on that channel")


def ERR_NOTREGISTERED(target):
    return _M(target, "451", "You have not registered")


def ERR_NEEDMOREPARAMS(command, target):
    return _M(target, "461", command, "Not enough parameters")


def ERR_ALREADYREGISTRED(target):
    return _M(target, "462", "You may not reregister")
