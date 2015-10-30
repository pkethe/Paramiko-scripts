__author__ = 'Pranav'

import paramiko
import time
import sys

# Specify Code Path
codePath = '/users/pkethe/test_build/';
dataPath = '/users/pkethe/test_build/data/';
localPath = '/Users/Pranav/Desktop/mnlr_data/'

# Specify Number of MNLR nodes to SSH
numOfMNLRNodes = 9

# Specify Number of IP Domain nodes to SSH
numOfIPNodes = 2

# Topology Name
topologyName = 'optimus'

# Assign Node Tier Configurations
mnlrTierAddress = []
mnlrTierAddress.append('1.1')               #node1
mnlrTierAddress.append('1.2')               #node2
mnlrTierAddress.append('1.3')               #node3
mnlrTierAddress.append('1.4')               #node4
mnlrTierAddress.append('2.1.1')             #node5
mnlrTierAddress.append('2.1.2')             #node6
mnlrTierAddress.append('2.1.3,2.2.1')       #node7
mnlrTierAddress.append('2.2.2')             #node8
mnlrTierAddress.append('2.3.1')             #node9

# Assign End Network Node IDS
endNWNodeIDS =[5,9];
endNWIPS = ['10.1.9.3', '10.1.8.3'];
endNWCIDR = ['24','24', '24']
endInterfaces =[];
endNodeSSH = [];

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
    ssh[i].connect(hostNames[i], port=22, username='pkethe', password='PWD');
    sys.stdout.write("\rConnected: %s" % hostNames[i]);
    sys.stdout.flush();

    # first do cleanup, just incase if previous configurations exist
    stdin, stdout, stderr = ssh[i].exec_command('sudo pkill tshark');
    stdin, stdout, stderr = ssh[i].exec_command('sudo pkill hello');
    stdin, stdout, stderr = ssh[i].exec_command('ps -ef | grep hello');
    stdin, stdout, stderr = ssh[i].exec_command('ps -ef | grep tshark');
    stdin, stdout, stderr = ssh[i].exec_command('rm -f' + dataPath + '*');

    print ''


# Connect each MNLR Node, and run configurations
for i in range(0, numOfMNLRNodes):

    # Check interfaces where tshark has to be run
    stdin, stdout, stderr = ssh[i].exec_command('awk \'{print $1,$2}\' /var/emulab/boot/ifmap')
    output = stdout.readlines();

    # build tshark command

    tcmd = 'sudo tshark'
    for j in range(0, len(output)):
        temp = output[j].split(' ');
        if temp[1].rstrip() not in endNWIPS:
            tcmd += ' -i ' + temp[0];
        else:
            # Store end n/w interfaces.
            endInterfaces.append(temp[0]);

            # Store end n/w SSH details, have to change this if you have multiple end networks for each node.
            endNodeSSH.append(ssh[i]);

            #print "Ignoring end network" + temp[0] + " as it is a control IP"
            sys.stdout.flush();
    tcmd += ' -w '+ dataPath + 'node' + str(i+1) + '.pcap';
    print 'exec# ' + tcmd;

    # start tshark
    stdin, stdout, stderr = ssh[i].exec_command(tcmd);

    # build MNLR command
    mcmd ='sudo '+ codePath+ 'hello';

    # append tierAddrs
    tiers = mnlrTierAddress[i].split(',');

    for j in range (0, len(tiers)):
        mcmd += ' -T ' + tiers[j];

    # check if node is an end node
    if (i + 1) in endNWNodeIDS:
        mcmd += ' -N 0';
        print track
        print endNWIPS[track]
        print endNWCIDR[track]
        print endInterfaces[track]
        mcmd += ' ' + endNWIPS[track] + ' ' + endNWCIDR[track] + ' ' + endInterfaces[track];
        track +=1;
    else:
        mcmd += ' -N 1';

    mcmd += ' > /dev/null';
    print 'exec# '+ mcmd;

    # start mnlr_start
    stdin, stdout, stderr = ssh[i].exec_command(mcmd);

# Wait few seconds to stabilize
sys.stdout.flush();
sys.stdout.write("\rWaiting for all nodes to stabilize...")
time.sleep(10);
sys.stdout.flush();
sys.stdout.write("\rDone.\n")

# Bring down one of the end network.
print 'Bringing down interface now ' + endInterfaces[0];
stdin, stdout, stderr = endNodeSSH[0].exec_command('sudo ip link set dev ' + endInterfaces[0] + ' down')
time.sleep(5);

# Bring up
print 'Bringing up interface now ' + endInterfaces[0];
stdin, stdout, stderr = endNodeSSH[0].exec_command('sudo ip link set dev ' + endInterfaces[0] + ' up')
time.sleep(5);

# Bring down one of the end network.

print 'Bringing down interface second time' + endInterfaces[0];
stdin, stdout, stderr = endNodeSSH[0].exec_command('sudo ip link set dev ' + endInterfaces[0] + ' down')
time.sleep(5);

# Bring up
print 'Bringing up interface second time' + endInterfaces[0];
stdin, stdout, stderr = endNodeSSH[0].exec_command('sudo ip link set dev ' + endInterfaces[0] + ' up')
time.sleep(5);

# status
sys.stdout.flush();
sys.stdout.write("Converting captured pcaps to .csv");
stdin, stdout, stderr = endNodeSSH[0].exec_command( 'sudo chmod 777 ' + dataPath +'*.pcap')
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
password = "PWD"
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
                lineArray = line.split(',');

                dataArray = lineArray[5].split(':')

                # is MNLR type 5
                if dataArray[0] == '05':
                    if dataArray[2] == '01' or dataArray[2] == '02':
                        outfile.write(line)




sys.stdout.flush();
sys.stdout.write('\rMerged .csv files to single ' + filePath);

print ''

print ("Bye..")
