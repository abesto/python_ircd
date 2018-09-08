from include.numeric_responses import *


class Command(object):
    required_parameter_count: int = -1
    command = ""
    user_registration_command = False
    server_registration_command = False

    def __init__(self):
        self.cleanup()

    def cleanup(self):
        self.message = None
        self.actor = None
        self.user = None
        self.server = None

    def from_server(self, *args):
        raise NotImplementedError

    def from_user(self, *args):
        raise NotImplementedError

    def common(self, *args):
        raise NotImplementedError

    def handle(self, actor, message):
        self.cleanup()
        self.actor = actor
        self.message = message

        if self.required_parameter_count is None:
            raise NotImplementedError(
                "required_parameter_count must be set on Handler subclass"
            )
        if self.command is None:
            raise NotImplementedError("command must be set on Handler subclass")
        if self.command != message.command:
            raise "Wrong handler for " + repr(message)

        if not actor.is_user() and not actor.is_server():
            if self.user_registration_command:
                if self.server_registration_command:
                    return self.common()
                return self.from_user(*message.parameters)
            elif self.server_registration_command:
                return self.from_server(*message.parameters)
            else:
                return ERR_NOTREGISTERED(actor)

        if len(message.parameters) < self.required_parameter_count:
            return ERR_NEEDMOREPARAMS(self.command, actor)
        elif actor.is_server():
            self.server = self.actor.get_server()
            return self.from_server(*message.parameters)
        elif self.actor.is_user():
            self.user = self.actor.get_user()
            registered = self.user.registered.both
            if not (self.user_registration_command or registered):
                return ERR_NOTREGISTERED(self.actor)
            message.prefix = str(self.user)
            return self.from_user(*message.parameters)
        else:
            raise Exception("Don't know what to do :(")
