#!/usr/bin/env python3

#Script was Writtent by NetScout Premium Servicess
#Author James Vigliotti

#These classes/modules needed to run script
import pandas as pd
from datetime import datetime, timedelta
import os
from xml.etree import ElementTree
import sys
from getpass import getpass
import platform
import distro
import csv
import requests
from urllib3.exceptions import InsecureRequestWarning

#declarations
url = '/ng1api/ncm/devices'
url_open = '/ng1api/rest-sessions'
url_close = '/ng1api/rest-sessions/close'
file_xml = 'mib2add.xml'
def xml_file(name,ipaddress):
    xml_file = open('mib2add.xml',"wb")
#    xml query tree for production request
    tree = ElementTree.ElementTree()
    root = ElementTree.Element("DeviceConfigurations")
    networkobj = ElementTree.SubElement(root, "DeviceConfiguration")
    device_name = ElementTree.SubElement(networkobj, "DeviceName")

    auth.text = 'N3e9qG5FhK1b0LgqN3e9qG5FhK1b0Lg'
#    snmpv3.text = 'N3e9qG5FhK1b0LgqN3e9qG5FhK1b0Lg'
    auth_sn.text = 'SHA'
    is_priv.text = 'true'
    priv_prot.text = 'AES'
    priv_pass.text = 'G4mF4qbY1wP4H1efG4mF4qbY1wP4H1e'
    n_retries.text = '1'
    timeout.text = '3'
    device_alarm.text = 'true'
    add_net.text = 'true'
    ncm.text = 'false'

    tree = ElementTree.ElementTree(root)
    # writes Production xml file
    tree.write(xml_file, xml_declaration=True)

def curl_command(user_name, server_ip, server_port, nId):
    os.system('curl -k -X POST -u'+user_name+':'+nId+' https://'+server_ip+':'+server_port+'/dbonequerydata/query -H "Content-Type:application/xml" -H "Accept:text/csv" -d @alltraffic.xml -o alltraffic.csv')

def nG1_login_data():
    print('Gathering nG1 login data')
#    user_name = input('Please enter nG1 user id: ')
    server_ip = input('Please enter nG1 DGM/Standalone ip: ')
    server_port = input('Please enter the server port: ' )
    nId = getpass('Please enter password/nID: ')
#    network_id = input('Please enter network id to use: ' )
    return server_ip, server_port, nId


def rest_close():
    #using curl to close api session
    print('Closing API session cookie')
    # Cookie file path

    p_version = sys.version
    p_os = platform.platform()
    print('Script is running on '+p_os+' running python version '+p_version)
else:
    p_version = sys.version
    p_os = distro.name()
    p_dver = distro.version()
    print('Script is running on '+p_os+' '+p_dver+' running python version '+p_version)

# get Server data
server_ip, server_port, nId = nG1_login_data()
# Disable urllib3 warnings about insecure HTTPS requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

curl_api_open()

with open('mib2_upload.csv') as file_obj:
    # Skips the heading
    # Using next() method
    heading = next(file_obj)
    # Create reader object by passing the file
    # object to reader method
    reader_obj = csv.reader(file_obj)

    # Iterate over each row in the csv
    # file using reader object
    for row in reader_obj:
        name = row[0]
        ipaddress= row[1]
        xml_file(name,ipaddress)
        nG1_call()

rest_close()
