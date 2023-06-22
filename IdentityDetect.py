############################################
#Replace contents of maclist file with the complete output of show mac add before running
############################################


from paramiko import SSHClient
from paramiko import AutoAddPolicy
import time
from sys import exit
from pythonping import ping
import re
import signal 
from getpass import getpass
import socket

def sigint_handler(signal, frame):
    print ('\n\nUser Initiated Interrupt')
    if client:
        client.close()
    input('Press Enter to close.....')
    exit(0)
    quit()


def getMACList(file):
    file = open(file, 'r')
    macList = file.read().split('\n')
    return macList

###################################################################

if __name__ == '__main__':

    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    signal.signal(signal.SIGINT, sigint_handler)
    arp = False
    transport = False
    IPaddr = False
    macList = getMACList('maclist.txt')#list of macs and ports

    #Visual verification of loaded MAC addresses    
    for mac in macList:
        print (mac)
    print ('\n\nDevice list loaded. Ready to process\n')
    
    while not transport:
        unInput = input('Username: ')
        pwInput = getpass()
        if not IPaddr:
            IPaddr = input('Core Router/Switch IP: ')
        else:
            IPaddr = input(f'Core Router/Switch IP[{IPaddr}]: ') or IPaddr
        try:                   
            print ('Connecting to Core Device...Please Wait')
            client.connect(IPaddr, username=unInput, password=pwInput)
            transport = client.get_transport()
            transport.send_ignore()
        except:
            print ("Authentication Failed. Please Retry")
        
    print ('Connection Established. Gathering Information.')
    channel = client.invoke_shell()
    
    for macLine in macList:
        macAddr = re.search('([0-9a-f]{4}[\.][0-9a-f]{4}[\.][0-9a-f]{4})', macLine) #extract mac address from single line using regex

        try:
            channel.send(f'show ip arp {macAddr.group(0)}\n')   
        except:
            input (f'\nERROR: Mac format not detected [0000.0000.0000]. Following line not imported\n\n{macLine}')
            
        
        while not channel.recv_ready():
            time.sleep(1)
        out = channel.recv(9999)
        
        while not arp:
            time.sleep(1)
            
            try:
                #verify we've returned usable data before continuing
                arp = re.search("^show ip arp",out.decode("ascii")).group(0)
            except:
                arp = False
                out = channel.recv(9999)
                
        try:
            macIP = re.search("(([0-9][0-9][0-9]|[0-9][0-9]|[0-9])\.){3}([0-9][0-9][0-9]|[0-9][0-9]|[0-9])", 
                                                                            out.decode("ascii")).group(0)
            #requires tuple input. The first 0 is a placeholder for a port. Not sure what the second 0 is.
            record = socket.getnameinfo((macIP,0),0)
            print (f'{macLine}    {macIP}    {record[0]}')
        except:
            print (f'{macLine}    No IP found')
        
       
    client.close()
    
    input("\nPress any key to continue...")
    
