# -*- coding: utf-8 -*-
'''
Server Program used to handle multiple clients in a secure manner using
certificates and SSL/TLS protocol, store data
to the database. 

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
from threading import Thread
import queue
import threading
from collections import OrderedDict

listen_addr = '192.168.0.182'
listen_port = 8082
server_cert = 'server.crt'
server_key = 'server.key'
client_certs = 'client_combine.crt'
threads = []
BUF_SIZE = 1024
dataQueue = queue.Queue(BUF_SIZE)
nodelist = []
firmWareLocation = ""
firmWareUpdate = ""
versionNumber = 1.1

################################################################################
# There are 2 threads running to handle communication with clients and process all
# the data coming from the clients
################################################################################
# DataThread processes all the data in the queue and pushes it to the database.
# this also check for the type of packet received
class DataThread(threading.Thread):      
    def __init__(self, group=None, target=None, name=None,args=(), kwargs=None, verbose=None):
        super(DataThread,self).__init__()
        self.target = target
        self.name = name
        
    # run function of this thread 
    def run(self):
        global firmWareUpdate
        global firmWareLocation
        global dataQueue
        global versionNumber
        idIndex = 1
        commandIndex = 2
        fieldIndex = 4
        while True:
            try:
                if not dataQueue.empty():
                    datarequest = (dataQueue.get())
                    requestField = str(datarequest).split('/')
                    print(requestField)
                    if requestField[idIndex].lower().strip() == 'pingpacket':
                        print("It is a ping packet")
                        # Store into database
                    elif requestField[idIndex].lower().strip() == 'datapacket':
                        print("It is a data packet")
                        # Store into database
                    elif requestField[idIndex].lower().strip() == 'update':
                        print("It is an update request")
                        firmWareUpdate = True
                        firmWareLocation = requestField[commandIndex]
                        versionNumber = requestField[fieldIndex]
                        print("Current Status:",firmWareUpdate)
                        print("Location",firmWareLocation)
                        print("Version Number",versionNumber)
                        for node in nodelist:
                            print("Updating nodes status for updating required")
                            node['Update'] = True
                        print(nodelist)
                    if (firmWareUpdate == True):
                        print("Checking if all nodes have been updated")
                        UpdateFlag = True
                        for node in nodelist:
                            print("Actual Node Status:" ,node['Update'])
                            if(node['Update'] == True):
                                UpdateFlag = False
                        print("UpdateFlag",UpdateFlag)
                        if(UpdateFlag == True):
                            print("All clients have been updated:")
                            firmWareUpdate = False
            except Exception as e:
                print("Exception ------->",e)
# ClientThread take care of connecting to each client by making instance of new thread 
# connection with client
class ClientThread(Thread): 
    
    def __init__(self,conn,ip,port): 
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        self.firstcontact = int(time.time()*1000)
        self.lastactivity = int(time.time()*1000)
        self.connected = True
        print("New server socket thread started for " + ip + ":" + str(port))
        nodeStatus=OrderedDict()
        nodeStatus['ip'] = self.ip
        nodeStatus['port'] = self.port
        nodeStatus['conn'] = self.conn
        nodeStatus['Update'] = False
        nodelist.append(nodeStatus)
        print("List of nodes:",nodelist)
        
    def run(self):
        global firmWareUpdate
        global firmWareLocation
        global versionNumber
        while True :
            print("Waiting for data from client")
            try:
                data = self.conn.recv(4096)
                data1 = data.decode()			
                if data1:
                    self.lastactivity = int(time.time()*1000)
                    print("Server received data:", data1)
                    print("Last activity at:",self.lastactivity)
                    print("thread running", self.name)
                    print("firmware update required:",firmWareUpdate)
                    if(firmWareUpdate == True):
                        print("Need to update client firmware")
                        for node in nodelist:
                            if(node['conn']==self.conn):
                                locationdata = '/Update/' + str(firmWareLocation) + '/version/' + str(versionNumber)
                                print("Sending firmware location" + locationdata)
                                self.conn.send(str(locationdata).encode())
                                node['Update'] = False
                                break
                    else:
                        self.conn.send("/Recieved".encode())
                    if not dataQueue.full():
                        dataQueue.put(data1)
                else:
                    print("Didn't get anything")
                    self.connected = False
                    self.conn.close()
                    for node in nodelist:
                        if (node['conn']==self.conn):
                            nodelist.remove(node)
            except Exception as error:
                print(error)
                self.connected = False
                self.conn.close()
                for node in nodelist:
                    if (node['conn']==self.conn):
                        nodelist.remove(node)
            if(self.connected == False):
                break
        print("Exiting thread")

        
# Start the datathread on starting of program       
datathread = DataThread(name='DataThread')
datathread.start()   
#Load certificates and necessary keys to create ssl instance 
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)
#create a socket connection and start listening on the port
bindsocket = socket.socket()
bindsocket.bind((listen_addr, listen_port))
bindsocket.listen(1)

#waiting for connections from clients
while True:
    try:
        print("Waiting for client")
        newsocket, fromaddr = bindsocket.accept()
        print("Client connected: {}:{}".format(fromaddr[0], fromaddr[1]))
        conn = context.wrap_socket(newsocket, server_side=True)
        print("SSL established. Peer: {}".format(conn.getpeercert()))
        newthread = ClientThread(conn,fromaddr[0], fromaddr[1]) 
        newthread.start() 
        threads.append(newthread)
        print("Active threads: ",threading.active_count())
    except Exception as error:
        print(error)

for t in threads: 
    t.join()
        
