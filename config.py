from datetime import datetime

listen_host = '0.0.0.0'
listen_port = 6667

servername = 'localhost'
created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Note: no timezone info
motd_file = 'motd.txt'

# Make message parsing less picky
traling_spaces = True       # Accept trailing spaces before EOL
soft_eol = True             # Accept either \r, \n or \r\n as EOL
lowercase_commands = True   # Accept lowercase commands (join instead of JOIN)
