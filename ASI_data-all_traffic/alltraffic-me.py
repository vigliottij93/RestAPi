!/usr/bin/env python3

#Script was Writtent by NetScout Premium Servicess
#Author James Vigliotti for  Steve Leventhal

#These classes/modules needed to run script

import pandas as pd
from datetime import datetime, timedelta
import os
from xml.etree import ElementTree
import sys
from getpass import getpass
import platform
import distro
import configparser

def xml_file():
  # Get the current time
    current_time = datetime.now()

    # Round down the minute part to the nearest multiple of 5 for both start and end times
    rounded_minutes = current_time.minute - (current_time.minute % 5)

    # Create new datetime objects with the rounded minutes
    rounded_start_time = current_time.replace(minute=rounded_minutes) - timedelta(hours = 1) #31 days.
    rounded_end_time = current_time.replace(minute=rounded_minutes)

    # Format the start and end times as needed
    start = rounded_start_time.strftime("%Y-%m-%d_%H:%M:%S")
    end = rounded_end_time.strftime("%Y-%m-%d_%H:%M:%S")
    print('Creating network service xml file for extracting application list volume')
    xml_file = open('api.xml',"wb")

#    xml query tree for production request
    tree = ElementTree.ElementTree()
    root = ElementTree.Element("GenericClientQuery")
    networkobj = ElementTree.SubElement(root, "NetworkObjectData")
    networkparm = ElementTree.SubElement(networkobj, "NetworkParameter")
    selectcolumn = ElementTree.SubElement(networkobj, "SelectColumnList")
    clientColumn = ElementTree.SubElement(selectcolumn, "ClientColumn")
    clientColumn1 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    clientColumn2 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    clientColumn3 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    clientColumn4 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    clientColumn5 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    flowfilter = ElementTree.SubElement(root, "FlowFilterList")
    flowfil = ElementTree.SubElement(flowfilter, "FlowFilter")
    flownet = ElementTree.SubElement(flowfil, "IPAddress")
    flowifn = ElementTree.SubElement(flowfil, "Ifn")
    filter = ElementTree.SubElement(flowfil, "FilterList")
    flowint = ElementTree.SubElement(filter, "srcAddress")
#    flowfil1 = ElementTree.SubElement(flowfilter, "FlowFilter")
#    filter2 = ElementTree.SubElement(flowfil1, "FilterList")
#    flownet2 = ElementTree.SubElement(filter2, "networkServiceId")
#    flowint2 = ElementTree.SubElement(filter2, "destAddress")
    functionlist = ElementTree.SubElement(root, "FunctionList")
    timedef = ElementTree.SubElement(root, "TimeDef")
    starttime = ElementTree.SubElement(timedef, "startTime")
    endtime = ElementTree.SubElement(timedef, "endTime")
    resolution = ElementTree.SubElement(timedef, "resolution")
    duration = ElementTree.SubElement(timedef, "duration")
#    this puts data in the xml tree for request
    networkparm.text = 'APPLICATION'
    clientColumn.text = 'appId'
    clientColumn1.text = 'octets'
    clientColumn2.text = 'destPort'
    clientColumn3.text = 'destAddress'
    clientColumn4.text = 'srcAddress'
    clientColumn5.text = 'srcPort'
    flownet.text = me_ip
    flowifn.text = me_ifn
    flowint.text = host_ip
#    flownet2.text = '175852513'
#    flowint2.text = src_address
    starttime.text = start
    endtime.text = end
    resolution.text = 'NO_RESOLUTION'
    duration.text = 'LAST_1_DAY'
    tree = ElementTree.ElementTree(root)
    # writes Production xml file
    tree.write(xml_file, xml_declaration=True)

def curl_command(server_ip, server_port, nId):
#    os.system('curl -k -X POST -u'+user_name+':'+nId+' https://'+server_ip+':'+server_port+'/dbonequerydata/query -H "Content-Type:application/xml" -H "Accept:text/csv" -d @alltraffic.xml -o alltraffic.csv')
    os.system('curl -k -X POST --cookie "NSSESSIONID='+nId+'" https://'+server_ip+':'+server_port+'/dbonequerydata/query -H "Content-Type:application/xml" -H "Accept:text/csv" -d @api.xml -o '+host_ip+'-traffic.csv')

def nG1_login_data():
  # Define the path for the config file
    config_file_path = '.config.ini'
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the configuration file
    config.read(config_file_path)
    # Access variables for script
    server_ip = config.get('settings', 'server_ip')
    server_port = config.get('settings', 'server_port')
    nId = config.get('settings', 'nId')
    me_ip = config.get('settings', 'me_ip')
    me_ifn = config.get('settings', 'me_ifn')
    host_ip = config.get('settings', 'host_ip')
    return server_ip, server_port, nId, me_ip, me_ifn, host_ip

def cleanup_csv():
    #Remove unwanted columns for final ouptu
    df = pd.read_csv(host_ip+'-traffic.csv')
    df = df[['srcAddress', 'srcPort','destAddress', 'destPort', 'octets', 'appId_String']]
    df.to_csv(host_ip+'-traffic_filtered.csv', index=False)
    print('This final version of requested data is as follows alltraffic_filtered.csv')
    print('Script completed')

if platform.system() =='Windows':
    p_version = sys.version
    p_os = platform.platform()
    print('Script is running on '+p_os+' running python version '+p_version)
else:
    p_version = sys.version
    p_os = distro.name()
    p_dver = distro.version()
    print('Script was tested on '+p_os+' '+p_dver+' running python version '+p_version)
server_ip, server_port, nId, me_ip, me_ifn, host_ip = nG1_login_data()
xml_file()
curl_command(server_ip, server_port, nId)
cleanup_csv()

