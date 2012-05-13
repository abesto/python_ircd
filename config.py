from datetime import datetime

listen_host = '0.0.0.0'
listen_port = 6667

servername = 'localhost'
created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Note: no timezone info
motd_file = 'motd.txt'