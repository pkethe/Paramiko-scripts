__author__ = 'Pranav'


import paramiko
import time
import sys

# Specify Number of MNLR nodes to SSH
numOfMNLRNodes = 5

# Specify Number of IP Domain nodes to SSH
numOfIPNodes = 3

# Topology Name
topologyName = 'top3'

# Create ssh sessions for numOfMNLRNodes.
ssh = []
for i in range (0, numOfMNLRNodes):
    ssh.append(paramiko.SSHClient())

# Connect to all MNLR Nodes and perform a cleanup
hostNames=[]
track = 0
for i in range(0, numOfMNLRNodes):
    ssh[i].set_missing_host_key_policy(paramiko.AutoAddPolicy())
    hostNames.append('node'+ str(i+1) + '.' + topologyName + '.fct.emulab.net');
    sys.stdout.write("\rConnecting: %s" % hostNames[i])
    sys.stdout.flush();
    ssh[i].connect(hostNames[i], port=22, username='pkethe', password='pwd');
    sys.stdout.write("\rConnected: %s" % hostNames[i]);
    sys.stdout.flush();

    if i == 0 :
        continue;

    # first do cleanup, just incase if previous configurations exist
    stdin, stdout, stderr = ssh[i].exec_command('cd /etc/; sudo chmod 777 ntp.conf; sudo sed -i \'13s/.*/server 155.98.39.138 iburst minpoll 6 maxpoll 6/\' ntp.conf');
    stdin, stdout, stderr = ssh[i].exec_command('sudo service ntp stop');
    stdin, stdout, stderr = ssh[i].exec_command('sudo service ntp start');
