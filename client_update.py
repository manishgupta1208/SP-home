# -*- coding: utf-8 -*-
'''
A client program which is used to pass the data related to updating 
new firmware to all connected clients 

@author: Manish Gupta <manishthaparian.gupta@gmail.com>
'''

# Copyright (C) 2018 Manish Gupta <manishthaparian.gupta@gmail.com>; 

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Manish Gupta <manishthaparian.gupta@gmail.com>"
__copyright__ = "Copyright 2018"
__credits__ = [ "Manish Gupta" ]
__license__ = "GPL"
__version__ = "1"
__maintainer__ = "Manish Gupta"
__email__ = "<manishthaparian.gupta@gmail.com>"
__status__ = "Prototype"
#!/usr/bin/python3

import socket
import ssl

host_addr = '192.168.0.182'
host_port = 8082
server_sni_hostname = 'Server'
server_cert = 'server.crt'
client_cert = 'client1.crt'
client_key = 'client1.key'
version = 1.1
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
clientsocket = None
conn = None
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn = context.wrap_socket(clientsocket, server_side=False, server_hostname=server_sni_hostname)
conn.connect((host_addr, host_port))
print("SSL established. Peer: {}".format(conn.getpeercert()))
if clientsocket:
    dataItem = '/Update/' + "www.example.com" +'/version/' + str(version)
    conn.send(dataItem.encode())
    conn.close()