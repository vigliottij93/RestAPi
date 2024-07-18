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
import xml.etree.ElementTree as ET
from tqdm import tqdm

#declarations
url = '/ng1api/ncm/devices'
#url_get ='/ng1api/ncm/devices/mydevice/'+name
url_open = '/ng1api/rest-sessions'
url_close = '/ng1api/rest-sessions/close'
file_xml = 'mib2add.xml'


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
    cookie_file = 'cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value

    # Perform POST request
    response = requests.post('https://'+server_ip+':'+server_port+url_close, cookies=cookies, verify=False)
    # Print response status code and content
    print('Response Status Code:', response.status_code)
    print('Completed, removing session cookie')
    os.system('rm cookie.txt')

def curl_api_open():
    print('Making API call to nG1 RESTAPI')
    # Request headers
    headers = { 'Content-Type': 'application/xml'
    }
    # Request data (if needed)
    # Cookie (if needed)
    cookies = { 'NSSESSIONID': nId
    }
    # Perform POST request
    response = requests.post('https://'+server_ip+':'+server_port+url_open, headers=headers, cookies=cookies, verify=False)
    print('Response Status Code:', response.status_code)
    print('Response Content:', response.text)
    print('Completed RESTAPI nG1 Call')
    # Save cookies to file if needed
    with open('cookie.txt', 'w') as f:
        for cookie in response.cookies:
            f.write(str(cookie.name) + '=' + str(cookie.value) + '\n')

def nG1_call_device_get():
    print('Pulling Device list from nG1')
    url_get ='/ng1api/ncm/devices/'
    # Request headers
    headers = {
        'Content-Type': 'application/xml'
    }

    # Cookie file path
    cookie_file = 'cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
    # Perform GET request
    response = requests.get('https://'+server_ip+':'+server_port+url_get, headers=headers, cookies=cookies, verify=False) 
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_get_response-error.xml', 'wb') as f:
            f.write(response.content)
    else:
        with open('nG1_get_response.xml', 'wb') as r_write:
            r_write.write(response.content)
    print('Finished Device list from nG1')

def file_count(file):
    file_path = file
    # Initialize line counter
    line_count = 0

    # Open the file and count lines
    with open(file_path, 'r') as file:
        for line in file:
            line_count += 1
    return line_count

def device_list():
#    print('Get creating device list to remove SDWAN routers from system')
    tree = ET.parse('nG1_get_response.xml')
    # Get the root element
    root = tree.getroot()
    for device in root.findall('DeviceConfiguration'):
        name = device.find('DeviceName').text
        s_name = device.find('nG1ServerName').text
        ip_add = device.find('DeviceIPAddress').text
        status = device.find('Status').text
        if ip_add == ipaddress:
            if s_name == 'monnpm01094p03' and status == 'Active':
                with open('device_keep.csv', 'a') as d_remove:   
                    print(name,ip_add,s_name, sep=',', file=d_remove)
            else:
                with open('device_removal.csv', 'a') as d_keep:
                    print(name,ip_add,s_name, sep=',', file=d_keep)

def call_remove():
    input_file = 'device_removal.csv'
    # Count total number of lines in the CSV file for the progress bar
    with open(input_file, 'r', newline='') as file:
        reader = csv.reader(file)
        num_lines = sum(1 for row in reader)

    # Use tqdm for a progress bar while reading lines
    with open(input_file, 'r', newline='') as file, \
            tqdm(total=num_lines, desc='Deleting Devices', unit='lines') as pbar:
        reader = csv.reader(file)
    
        for row in reader:
            # Process each row as needed
            with open('removed_devices.txt', 'a') as test_remove:
            # Example: Print the row (replace with your processing logic)
                device_name = row[0]
                router_remove(device_name)
                print(f'Removed device: {name}',file=test_remove)
                pbar.update(1)  # Update progress bar for each processed line


def router_remove(device_name):
    url_get ='/ng1api/ncm/devices/'+device_name
    # Request headers
    headers = {
        'Content-Type': 'application/xml'
    }

    # Cookie file path
    cookie_file = 'cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
#   call to delete device
    response = requests.delete('https://'+server_ip+':'+server_port+url_get, headers=headers, cookies=cookies, verify=False) 
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_removal_response-error.xml', 'a') as f:
            f.write(str(response.content))
    else:
        with open('nG1_removal_response.xml', 'a') as r_write:
            r_write.write(str(response.content))



if platform.system() =='Windows':
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
mib_cnt = file_count('mib2_upload.csv')
print(f'Number of SDWAN routers to check {mib_cnt}')
curl_api_open()
nG1_call_device_get()
print('Creating SDWAN router list to remove from nG1 ')
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
#        xml_file(name,ipaddress)
#        nG1_call()
#        nG1_call_device_get(ipaddress)
        device_list()
print('Finished SDWAN Device list')
rmove_cnt = file_count('device_removal.csv')
print(f'Device count to remove from nG1 Servers {rmove_cnt}')
keep_cnt = file_count('device_keep.csv')
print(f'Device count to remove from nG1 Servers {keep_cnt}')
print('Removing Devices from nG1')
call_remove()

rest_close()

