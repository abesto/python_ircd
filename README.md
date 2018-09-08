python-ircd [![Build Status](https://secure.travis-ci.org/abesto/python-ircd.png)](http://travis-ci.org/abesto/python-ircd)
===========

Aims to be a full-featured IRC server, started as a way to get some Python practice. The primary priority is complete support of the three RFCs describing the IRC protocol.

# Running, hacking
 1. Set up development environment with `make setup`
 1. Run the server with `make listen`
 1. Reformat code and run tests with `make`
 1. Update dependencies with `make update`
 
See the [`Makefile`](./Makefile) for additional targets you can use for more granular control.

# Status
The basic framework is mostly stable. Command handlers get an abstract message object, operate on the database, and return similar abstract message objects. The database currently consists of simplistic in-memory dictionaries. Messages are passed to the handlers and to the targets in a generic way. Incoming messages are parsed with pyparsing. No server-server communication yet.

 * [RFC2811 - Internet Relay Chat: Channel Management](http://www.irchelp.org/irchelp/rfc/rfc2811.txt): Channels are created as they are joined by users; nothing else is done yet
 * [RFC2812 - Internet Relay Chat: Client Protocol](http://www.irchelp.org/irchelp/rfc/rfc2812.txt):
  * NICK: 100%
  * USER: 100%
  * PART: 100%
  * JOIN: no channel key checking
  * PRIVMSG: no support for wildcards, some checks missing
  * WHO: multiple parameters not supported
  * TOPIC: some checks missing
  * QUIT: no PART messages
 * [RFC2813 - Internet Relay Chat: Server Protocol](http://www.irchelp.org/irchelp/rfc/rfc2813.txt): 0%

# Dependencies
Development environment, you need to install these yourself on your system:
 * `pipenv`: dependency management
 * `make`: simple way to run tasks
 
Code quality tools, set up by `make setup` via `pipenv`:
 * `nose`, `mock`: for tests, obviously
 * `asynctest`: less painful testing when `asyncio` is involved
 * `mypy`: static type checking
 * `pylint`: code quality
 * `black`: code formatting

Used libraries (also set up by `make setup` via `pipenv`):
 * `dnspython3`: Reverse DNS lookups
 * `pyparsing`: Parsing incoming messages
 * `PyDispatcher`: Notifying parts of the system to runtime config changes

