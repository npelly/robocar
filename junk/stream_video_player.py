import socket
import subprocess
import shlex

# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 8001))
server_socket.listen(0)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rb')
print "hellocurl world"

try:
    # Run a viewer with an appropriate command line. Uncomment the mplayer
    # version if you would prefer to use mplayer instead of VLC
    #command = '/Applications/VLC.app/Contents/MacOS/VLC --play-and-exit --demux h264 -'
    command = '/Applications/VLC.app/Contents/MacOS/VLC --play-and-exit --demux h264 udp://@0.0.0.0:8002'

    #command = "/usr/local/bin/gst-launch-1.0 fdsrc fd=0 ! h264parse ! queue ! autovideosink"
    cmdline = shlex.split(command)
    #cmdline = ['mplayer', '-fps', '25', '-cache', '1024', '-']
    player = subprocess.Popen(cmdline, stdin=subprocess.PIPE)
    print "hello world"
    while True:
        # Repeatedly read 1k of data from the connection and write it to
        # the media player's stdin
        data = connection.read(1024)
        if not data:
            break
        player.stdin.write(data)
finally:
    connection.close()
    server_socket.close()
    player.terminate()
