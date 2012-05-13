from datetime import datetime

servername = 'localhost'
created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Note: no timezone info
motd_file = 'motd.txt'