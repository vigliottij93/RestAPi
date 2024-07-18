#!/usr/bin/env python3
#importing the module

import time
import json
from datetime import datetime, timedelta
#import csv
import sys
import os
import requests
#from xml.etree import ElementTree
import lxml.etree as etree
import paramiko
import socket
import time
import configparser
import platform
import distro

#script definitions
def config_files():
    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read('.config.ini')

    # SSH connection details
    port = config.getint('ssh', 'port')
    username = config.get('ssh', 'user1')
    # server connection details
    nid = config.get('server', 'nId')
    server_ip = config.get('server', 'server_ip')
    server_port = config.getint('server', 'server_port')
    uriRESTapiDevice = config.get('server', 'uriRESTapiDevice')
    #folder info
    folder_name = config.get('folder', 'folder_name')
    folder_pfs = config.get('folder', 'folder_pfs')
    folder_mobile = config.get('folder', 'folder_mobile')
    return  port, username, nid, server_ip, server_port, uriRESTapiDevice, folder_name, folder_pfs, folder_mobile

def scp_file_from_remote(hostname, username, remote_file_path, local_file_path):
    # Create SSH client instance
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    timeout = 5
    try:

       ssh_client.connect(hostname, username=username, timeout=timeout)
        # SCPClient from paramiko to transfer files
       scp_client = ssh_client.open_sftp()
       scp_client.get(remote_file_path, local_file_path)
       scp_client.close()

       print(f"File copied successfully from {hostname}:{remote_file_path} to {local_file_path}")

    except paramiko.AuthenticationException as auth_err:
        print(f"Authentication failed: {auth_err}")
    except paramiko.SSHException as ssh_err:
        print(f"SSH connection error: {ssh_err}")
    except FileNotFoundError as file_err:
        print(f"File not found: {file_err}")
    except Exception as e:
        print(f"Error copying file: {e}")

    finally:
        # Close SSH connection
        ssh_client.close()

def python_ver():
    if platform.system() =='Windows':
        p_version = sys.version
        p_os = platform.platform()
        print('Script is running on '+p_os+' running python version '+p_version)
    else:
        p_version = sys.version
        p_os = distro.name()
        p_dver = distro.version()
        print('Script is running on '+p_os+' '+p_dver+' running python version '+p_version)

def nG1_Device_call(user1, nId, server_ip, server_port, uriRESTapiDevice, folder_name, folder_pfs, folder_mobile):
    #checks for the  output directory
    print("starting ISNG/INFINISTEAM backups")
    requests.packages.urllib3.disable_warnings()
    cookies_dict = {"NSSESSIONID": nId}
    headers = {
        'Content-Type': 'application/xml',
    }
    response = requests.get('https://'+server_ip+':'+str(server_port)+uriRESTapiDevice , headers=headers, verify=False, cookies=cookies_dict)
    # inline data read the  response from nG1 for All servers
    root = etree.fromstring(response.content)

    #This reads the xml response  parses file to seperate csv files.
    for act_data in root.findall('DeviceConfiguration'):
        # access element - name
        device_name = act_data.find('DeviceName').text
        device_ip = act_data.find('DeviceIPAddress').text
        if 'InfiniStream' in act_data.find('DeviceType').text:
            if not os.path.exists(folder_name+"/"+device_name):
                os.makedirs(folder_name+"/"+device_name)
            else:
                print("Folder "+folder_name+"/"+device_name+" exists")
            folder_time = datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p")
            os.makedirs(folder_name+"/"+device_name+"/"+folder_time)
            confgxml = '/opt/NetScout/rtm/config/configfile.xml' 
            confgxml_l = folder_name+"/"+device_name+"/"+folder_time+'/configfile.xml'
            scp_file_from_remote(device_ip, user1, confgxml, confgxml_l)
            iptbl = '/etc/sysconfig/iptables'
            iptbl_l = folder_name+"/"+device_name+"/"+folder_time+'/iptables'
            scp_file_from_remote(device_ip, user1, iptbl, iptbl_l)
            afm_mode = '/opt/NetScout/rtm/bin/.afm_mode'
            afm_mode_l = folder_name+"/"+device_name+"/"+folder_time+'/.afm_mode'
            scp_file_from_remote(device_ip, user1, afm_mode, afm_mode_l)
            # if you  are using PFS mode uncomment lines below
            '''
            os.makedirs(folder_name+"/"+device_name+"/"+folder_pfs)
            pfs_f = '/opt/NetScout/rtm/bin/pfs.cfg'
            pfs_f_l = folder_name+"/"+device_name+"/"+folder_time+'/pfs.cfg
            scp_file_from_remote(device_ip, user1, pfs_f, pfs_f_l)
            '''
    '''      
        elif 'vSTREAM' in act_data.find('DeviceType').text:
            if not os.path.exists(folder_name+"/"+device_name):
                os.makedirs(folder_name+"/"+device_name)
            else:
                print("Folder "+folder_name+"/"+device_name+" exists")
            folder_time = datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p")
            os.makedirs(folder_name+"/"+device_name+"/"+folder_time)
            confgxml = '/opt/NetScout/rtm/config/configfile.xml' 
            confgxml_l = folder_name+"/"+device_name+"/"+folder_time+'/configfile.xml'
            scp_file_from_remote(device_ip, user1, confgxml, confgxml_l)
            iptbl = '/etc/sysconfig/iptables'
            iptbl_l = folder_name+"/"+device_name+"/"+folder_time+'/iptables'
            scp_file_from_remote(device_ip, user1, iptbl, iptbl_l)
            afm_mode = '/opt/NetScout/rtm/bin/.afm_mode'
            afm_mode_l = folder_name+"/"+device_name+"/"+folder_time+'/.afm_mode'
            scp_file_from_remote(device_ip, user1, afm_mode, afm_mode_l)
            # if you  are using PFS mode uncomment lines below
            os.makedirs(folder_name+"/"+device_name+"/"+folder_pfs)
            pfs_f = '/opt/NetScout/rtm/bin/pfs.cfg'
            pfs_f_l = folder_name+"/"+device_name+"/"+folder_time+'/pfs.cfg
            scp_file_from_remote(device_ip, user1, pfs_f, pfs_f_l)
     '''
#        elif 'vSTREAM Agent' in act_data.find('DeviceType').text:
#            print('vSTREAM Agents we dont have root access and will not be backup')
python_ver()
port, user1, nid, server_ip, server_port, uriRESTapiDevice, folder_name, folder_pfs, folder_mobile = config_files()
nG1_Device_call(user1, nid, server_ip, server_port, uriRESTapiDevice, folder_name, folder_pfs, folder_mobile)
