#!/usr/bin/env python3



#python modules to use
import pandas as pd
from datetime import datetime, timedelta
import os
from xml.etree import ElementTree
import sys
import pathlib
from cryptography.fernet import Fernet
import getpass
import requests
import argparse
from timeit import default_timer as timer
# pretty printing xml response fron nG1
from lxml import etree
import datetime
from http.cookiejar import MozillaCookieJar
from urllib3.exceptions import InsecureRequestWarning
import xml.etree.ElementTree as ET
import json
import csv

url = '/ng1api/ncm/devices'
url_device =  '/ng1api/ncm/devices/{name}'
url_app = '/ng1api/ncm/applications'
server_ip = '192.168.3.1'
server_port =  '8443'
nID = 'NIrf5nxRc+2Z7qehlAej+ytm2wu+jx0DoThZeI3yvOb0s/Wm9B/RJSNVjfK5S/3E1kMGxs+AXEVpbP2TS9LxseqBmyR+cqiWSKJw2HcvICs='

def rest_close1():
   print('Closing API session cookie')
   rest_close = os.popen('curl -X POST -b cookie.txt -k https://'+server_ip+':'+server_port+'/ng1api/rest-sessions/close').read()
   #print(rest_close)
   print('Completed, removing session cookie')

def curl_api_open():
    print('Making RESTAPI session cookie')
    curl_text = f'curl -X POST --cookie "NSSESSIONID={nID}" -k https://{server_ip}:{server_port}/ng1api/rest-sessions -c cookie.txt -H "Content-Type:application/xml"'
    #print(curl_text)
    rest_session = os.popen(curl_text).read()
    #print(rest_session)
    print('Completed RESTAPI session cookie')

def nG1_call_json():
    print('Pulling all Devices list from nG1')
    url_get ='/ng1api/ncm/devices/'
    # Request headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Cookie file path
    cookie_file = 'cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            # Split the line into fields
            fields = line.strip().split('\t')
            
            # The name of the cookie is the seventh field, and the value is the eighth field
            if len(fields) == 7:
                domain, flag, path, secure, expiration, name, value = fields
                cookies[name] = value
    # Perform GET request
    response = requests.get('https://'+server_ip+':'+server_port+url_get, headers=headers, cookies=cookies, verify=False) 
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_device_list-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open('nG1_device_list.json', 'wb') as r_write:
            r_write.write(response.content)
    print('Finished Device list from nG1. \t  nG1_device_list.json total {} bytes '.format(len(response.content)))


def nG1_call_dev_json(name):
    print('Pulling Device device info from nG1')
#    url_get ='/ng1api/ncm/devices/'
    url_device =  '/ng1api/ncm/devices/{name}'
    # Request headers
    headers = {
        'Content-Type': 'application/json'
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
    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{name}', headers=headers, cookies=cookies, verify=False) 
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_device_list-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open('nG1_device_'+name+'.json', 'wb') as r_write:
            r_write.write(response.content)
    print(f'Finished Device from nG1')

def nG1_call_dev_ifn_json(name):
    print(f'Pulling Device interface info for {name} from nG1')
#    url_get ='/ng1api/ncm/devices/'
    url_device =  f'/ng1api/ncm/devices/{name}/interfaces'
    # Request headers
    headers = {
        'Content-Type': 'application/json'
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
#    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{name}', headers=headers, cookies=cookies, verify=False) 
    response = requests.get(f'https://{server_ip}:{server_port}'+url_device, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_device_list-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open('nG1_device_'+name+'_ifn.json', 'wb') as r_write:
            r_write.write(response.content)
    print(f'Finished Device interface info for {name} from nG1')

def device_list(d_user): 
    print(f'Getting devices with the snmp V3 user {d_user}')
    json_file = 'nG1_device_list.json'
    # Read JSON file
    with open(json_file, 'r') as file:
        json_data = json.load(file)    
#    data = json.load('nG1_device_list.json')
    
    device_configurations = json_data['deviceConfigurations']
    # Step 3: Prepare to write to CSV file
    csv_file = 'device-list.csv'
    csv_columns = ['deviceName', 'deviceIPAddress']
    # Step 4: Write data to CSV file
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for device in device_configurations:
            if device['deviceType'] == 'Router/Switch':
                if 'userName' in device and device['userName'] == d_user:
                    writer.writerow({
                        'deviceName': device['deviceName'],
                        'deviceIPAddress': device['deviceIPAddress'],
                    })
    print(f'Finished device list for  V3 user {d_user}')

def deactivate_interface(name,ifn_id):
    print(f'Deactivating  Device interface {ifn_id} for {name} from nG1')
#    url_get ='/ng1api/ncm/devices/'
    url_device_dact =  f'/ng1api/ncm/devices/{name}/interfaces/{ifn_id}/deactivate'
    # Request headers
    headers = {
        'Content-Type': 'application/json'
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
#    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{name}', headers=headers, cookies=cookies, verify=False) 
    response = requests.post(f'https://{server_ip}:{server_port}{url_device_dact}', headers=headers, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:   
        with open('nG1_device_ifn_deactivate-error.json', 'a') as f:
            f.write(response.text)
    else:
        with open('response_'+name+'_ifn_deactive.json', 'a') as r_write:
            r_write.write(response.text)
    print(f'Finished Device interface info for {name} to nG1')

def change_ifn(name,json_sv):
    print(f'Device interface changesfor {name} to nG1')
#    url_get ='/ng1api/ncm/devices/'
    url_device_update =  f'/ng1api/ncm/devices/{name}/interfaces/'
    # Request headers
    headers = {
        'Content-Type': 'application/json'
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
    with open(json_sv, 'r') as f:
        data = f.read()
    # Perform GET request
#    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{name}', headers=headers, cookies=cookies, verify=False)
    response = requests.put(f'https://{server_ip}:{server_port}{url_device_update}', headers=headers, data=data, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:
        with open(name+'_ifn_change-error.json', 'w') as f:
            f.write(response.text)
    else:
        with open(name+'_ifn_change.json', 'w') as r_write:
            r_write.write(response.text)
    print(f'Finished Device interface change for {name} to nG1')

def device_mod_int(name): 
    print(f'Modifying device ifn(s) for {name}')
    json_file = 'nG1_device_'+name+'_ifn.json'
    json_sv = 'mod_ifn_'+name+'.json'
    # Read JSON file
    with open(json_file, 'r') as file:
        json_data = json.load(file)    
#    data = json.load('nG1_device_list.json')
    
    ifn_change = json_data['interfaceConfigurations']
    for int in ifn_change:
        if int['interfaceName'] == 'ge0/0':
             int['alias'] = 'LTE VPN'
        elif int['interfaceName'] == 'ge0/2.100':
             int['alias'] = 'TLOC INET from RO2'
        elif int['interfaceName'] == 'ge0/2.200':
             int['alias'] = 'MPLS Pass Through to R02Ge0/3.10 [PC/Priners]'
        elif int['interfaceName'] == 'ge0/3.131':
             int['alias'] = 'Gas POS'
        elif int['interfaceName'] == 'ge0/3.137':
             int['alias'] = 'Gas POS Servers'
        elif int['interfaceName'] == 'ge0/3.20':
             int['alias'] = 'ESX Server Management'
        elif int['interfaceName'] == 'ge0/3.24':
             int['alias'] = 'ESX Server Management'
        elif int['interfaceName'] == 'ge0/3.302':
             int['alias'] = 'Meraki'
        elif int['interfaceName'] == 'ge0/3.60':
             int['alias'] = 'POS'
        elif int['interfaceName'] == 'ge0/3.48':
             int['alias'] = 'Infastructure Management'
        elif int['interfaceName'] == 'ge0/3.70':
             int['alias'] = 'Pharmacy'
        elif int['interfaceName'] == 'ge0/4':
             int['alias'] = 'Router 2 Biz - Internet/DIA Circuit'
        elif int['interfaceName'] == 'Gi1   GigabitEthernet1':
             int['alias'] = 'Internal DHCP Internet Access'
#        else:
#            int['status'] = 'INACTIVE'
        else:
            ifn_id = int['interfaceNumber'] 
            deactivate_interface(name,str(ifn_id))
    with open(json_sv, 'w') as file:
        json.dump(json_data, file, indent=4)
    change_ifn(name,json_sv)
    print(f'Completed device ifn(s) for {name}')

def process_csv_file(file_path):
    try:
        # Open the CSV file for reading
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            
            # Iterate over each row in the CSV
            for row in reader:
                name = row['deviceName'] # row['name'] if file has header
                # Call your processing function here (example)
#                process_data(name, age, city)
                print('starting') 
                nG1_call_dev_ifn_json(name)
                device_mod_int(name)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"Error processing file '{file_path}': {e}")


#Script definition calls
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
#opens the cookie to make multiple calls
curl_api_open()
nG1_call_json()
# this gets devece name and ip addres for specific user cspc
d_user = input('Please enter snmpv3 user : ')
device_list(d_user)
#this get the router/switch basic info
#nG1_call_dev_json(name)
#this gets the devices iterfaces
#nG1_call_dev_ifn_json(name)
#this modifys device interfaces
#device_mod_int(name)
#code for add to send modify code to nG1
process_csv_file('device-list.csv')
#closes the restapi cookie
rest_close1()


