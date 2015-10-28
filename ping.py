__author__ = 'Pranav'

import paramiko
import time
import sys

dataPath = '/users/pkethe/test_build/data/';
localPath = '/Users/Pranav/Desktop/mnlr_data/'

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

# Connect each MNLR Node, and run configurations
for i in range(0, numOfMNLRNodes):
    # Check interfaces where tshark has to be run
    stdin, stdout, stderr = ssh[i].exec_command('awk \'{print $1,$2}\' /var/emulab/boot/ifmap')
    output = stdout.readlines();

    # build tshark command

    tcmd = 'sudo tshark'
    for j in range(0, len(output)):
        temp = output[j].split(' ');
        tcmd += ' -i ' + temp[0];

    tcmd += ' -w '+ dataPath + 'node' + str(i+1) + '.pcap';
    print 'exec# ' + tcmd;

    # start tshark
    stdin, stdout, stderr = ssh[i].exec_command(tcmd);

for i in range(0, numOfMNLRNodes):
    stdin, stdout, stderr = ssh[i].exec_command('ntpq -p | tail -1 | awk \'{print $9}\'');

    output = stdout.readlines();

    print repr(float(output[0])/1000);

time.sleep(40);
# status
sys.stdout.flush();
sys.stdout.write("Converting captured pcaps to .csv");
print ''
for i in range(0, numOfMNLRNodes):
    pcap2csvcmd = 'sudo tshark -r ' + dataPath + 'node' +  str(i+1) +'.pcap -T fields -E separator=, -e frame.time_epoch -e frame.interface_id -e eth.type -e frame.number -e data.data > ' + dataPath + 'node' + str(i+1) +'.csv';
    print pcap2csvcmd
    stdin, stdout, stderr = ssh[i].exec_command(pcap2csvcmd)

sys.stdout.flush();
sys.stdout.write("\rConverted captured pcaps to .csv");

print('');

# copy all remote .csv files to local folder.
transport = paramiko.Transport((hostNames[0], 22));
password = "pwd"
username = 'pkethe'
transport.connect(username=username, password=password)
sftp = paramiko.SFTPClient.from_transport(transport);
stdin, stdout, stderr = ssh[0].exec_command('sudo chmod 777' + dataPath + "*" )
for i in range(0 , numOfMNLRNodes):

    sftp.get(dataPath+'node'+str(i+1)+'.csv', localPath +'node'+str(i+1)+'.csv')

sftp.close()

# Merge all .csv files to one file.
sys.stdout.flush();
#final path file
filePath = localPath+'final.csv'
sys.stdout.write('\rMerging... .csv files to single ' + filePath);

with open(filePath, 'w') as outfile:
    for i in range(0, numOfMNLRNodes):
        with open(localPath+'node' + str(i+1) + '.csv') as infile:
            for line in infile:
                line = str(i+1) + ',' + line
                outfile.write(line);




sys.stdout.flush();
sys.stdout.write('\rMerged .csv files to single ' + filePath);

print ''

print ("Bye..")
