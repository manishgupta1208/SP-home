# -*- coding: utf-8 -*-
'''
Client program make connection to server and pushing the data 
to the server at regular intervals. 

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
import time
import threading
import queue
import random 

host_addr = '192.168.0.182'
host_port = 8082
server_sni_hostname = 'Server'
server_cert = 'server.crt'
client_cert = 'client.crt'
client_key = 'client.key'
BUF_SIZE = 1024
dataQueue = queue.Queue(BUF_SIZE)
pingQueue = queue.Queue(BUF_SIZE)
program_version =  1.0 

################################################################################
# PanelDataThread creates all the dummy data which needs to be sent to server 
# and push it to the queue
class PaneldataThread(threading.Thread):
    
    def __init__(self, group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(PaneldataThread,self).__init__()
        self.target = target
        self.name = name
    
    # run function of this thread 
    def run(self):
        print('Running PaneldataThread thread')
        currentTime = int(round(time.time() * 1000))
        batchstoreTime = int(round(time.time() * 1000))
        previousTime = 0
        pingTime = 0
        dataItem = '/DataPacket/'+'Gateway/' + 'Client1'
        while True:
            currentTime = int(round(time.time() * 1000))
            if(currentTime - pingTime >= 60000*5):
                pingTime = currentTime
                dataItem1 = '/PingPacket/' + 'Gateway/' + 'Client1' + '/Timestamp/' + str(currentTime) + '/version/' + str(program_version)
                if not pingQueue.full():
                    print("Sending ping data")
                    pingQueue.put(dataItem1)
                    print("dataItem1")
            if (currentTime - previousTime >= 1000):
                previousTime = currentTime
                if(currentTime - batchstoreTime >= 30000):
                    batchstoreTime = currentTime
                    dataItem = dataItem + '/Timestamp/' + str(currentTime) + '/SolarIrradiance/' + str(int(random.uniform(0, 100))) + '/Current/' + str(int(random.uniform(0, 10)))
                    print(dataItem)
                    if not dataQueue.full():
                        dataQueue.put(dataItem)
                        print("Length of data",len(dataItem))
                        dataItem = '/DataPacket/'+'Gateway/' + 'Client1'
                else:
                    dataItem = dataItem + '/Timestamp/' + str(currentTime) + '/SolarIrradiance/' + str(int(random.uniform(0, 100))) + '/Current/' + str(int(random.uniform(0, 10)))
                    print("Adding to batch")
#Start sonal panel fetch data thread
paneldata = PaneldataThread(name='Paneldata')
paneldata.start()
#Load certificates and necessary keys to create ssl instance 
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
clientsocket = None
conn = None
while True:
    try:
        if clientsocket:
            if not dataQueue.empty():
                print("Data Queue not empty")
                pidatarequest = (dataQueue.get())
                conn.send(pidatarequest.encode())
                data = conn.recv(2048)
                data = data.decode('utf-8')
                print(data)
            if not pingQueue.empty():
                print("Ping Queue not empty")
                pingdata = pingQueue.get()
                conn.send(pingdata.encode())
                data = conn.recv(2048)
                data = data.decode('utf-8')
                print(data)
                datafield = str(data).split('/')
                if datafield[1].lower().strip() == 'update':
                    print(datafield[4].lower().strip())
                    print(program_version)
                    if (float(datafield[4].lower().strip())!=float(program_version)):
                        print("update program")
                        print("Link is",datafield[2])
                        # Run script to download the program and restart the program
        else:
            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsocket.settimeout(5)
            conn = context.wrap_socket(clientsocket, server_side=False, server_hostname=server_sni_hostname)
            conn.connect((host_addr, host_port))
            print("SSL established. Peer: {}".format(conn.getpeercert()))
    except socket.timeout as e1:
        print("Got timeout error")
    except Exception as e:
        print("Connection error")
        print("Exception ------->",e)
        print("Sleeping for 1 min")
        clientsocket.close()
        clientsocket = None
        conn = None
        time.sleep(10)
    