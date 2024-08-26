#!/usr/bin/env python3

#Script was Writtent by NetScout Premium Servicess
#Author James Vigliotti

#These classes/modules needed to run script
import pandas as pd
from datetime import datetime, timedelta
import json
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
import configparser
from pathlib import Path
import paramiko
import time
import subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging
from colorama import Fore, Style, init
import tarfile
from datetime import datetime
import logging
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

#declarations
url = '/ng1api/ncm/devices'
#url_get ='/ng1api/ncm/devices/mydevice/'+name
url_open = '/ng1api/rest-sessions'
url_close = '/ng1api/rest-sessions/close'
file_xml = 'mib2add.xml'

#List of Variables, output folders and files
folder = 'restapi'
folder_time = datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p")
output_folder = folder +'/'+ folder_time
xml_dir = output_folder+'/xml'
xml_file =xml_dir+'/pkt_drip_ntksvc.xml'
log_dir = folder+'/log'
log_filename = log_dir+'/restapi_vital_drp_pkts.log'

def new_dir(folder_name):
    path = os.path.join(".", folder_name)
    try:
        os.mkdir(path)
        #print(f"Directory '{folder_name}' created.")
        logger.info(f"Directory '{folder_name}' created.")
    except FileExistsError:
        #print(f"Directory '{folder_name}' already exists.")
        logger.info(f"Directory '{folder_name}' already exists.")

def create_dirs():
    new_dir(folder)
    new_dir(output_folder)
    new_dir(xml_dir)
    new_dir(log_dir)


def curl_command(nid, server_ip, server_port):
    os.system(f'curl -k -X POST -u jvigliotti:Bat#cave0524 -k https://{server_ip}:{server_port}/dbonequerydata/query -H "Content-Type:application/xml" -H "Accept:text/json" -d @{xml_file} -o vitalsigns_drp-json.json')

def nG1_call_drops(server_ip, server_port, xml_in_file, xml_output_file):
    # Suppress the warning
    warnings.simplefilter('ignore', InsecureRequestWarning)
    nid = 'vluxoT80NIg+Rq6rFewiFC/36XvUnnb26K6LK3lcGGw4h+ms/bXXxmbxVrY4g0u/kz8Vyt2fOeBf/QaQjCAeXUhTagCczdSuafHuF+wTojDjtMxO156KXZ1BV8w5FV7N'
    cookies = {f'NSSESSIONID':'vluxoT80NIg+Rq6rFewiFC/36XvUnnb26K6LK3lcGGw4h+ms/bXXxmbxVrY4g0u/kz8Vyt2fOeBf/QaQjCAeXUhTagCczdSuafHuF+wTojDjtMxO156KXZ1BV8w5FV7N'}
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'text/csv',
    }
    with open(xml_in_file) as f:
        data = f.read().replace('\n', '').replace('\r', '').encode()
    response = requests.post(f'https://{server_ip}:{server_port}/dbonequerydata/query', cookies=cookies, headers=headers, data=data, verify=False)
    if response.status_code == 200:
        with open(xml_output_file, 'wb') as f:
            f.write(response.content)
        final_output('vitalsigns_drp_pkts.csv')
        nG1_call_get_devices(server_ip, server_port)
        add_device_name('filtered_output.csv', server_ip, server_port)
        
    else:
        logger.critical(response.text)

def nG1_call_get_devices(server_ip, server_port):
    cookies = {f'NSSESSIONID':'vluxoT80NIg+Rq6rFewiFC/36XvUnnb26K6LK3lcGGw4h+ms/bXXxmbxVrY4g0u/kz8Vyt2fOeBf/QaQjCAeXUhTagCczdSuafHuF+wTojDjtMxO156KXZ1BV8w5FV7N'}
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/', cookies=cookies, headers=headers, verify=False)
    if response.status_code == 200:
        with open('device-list.json', 'wb') as f:
            f.write(response.content)
    else:
        logger.critical(response.text)

def add_device_name(i_file, server_ip, server_port):
    input_file = i_file  # The input CSV file name
    df = pd.read_csv(input_file)
    json_file = 'device-list.json'  # The JSON file path containing device configurations
    output_csv_file = 'ISNG_drops.csv'

    # Dictionary to map IP addresses to device names
    ip_to_device_name = {}

    # Populate the dictionary with IP addresses and corresponding device names
    for ip in df['ipAddress'].tolist():
        device_name = get_device_name_from_ip(ip, json_file)
        if device_name:
            ip_to_device_name[ip] = device_name
            logger.info(f"IP: {ip}, Device Name: {device_name}")
        else:
            logger.warning(f"Device name not found for IP: {ip}")

    # Update the CSV with device names and interface names
    update_csv_with_interface_name(input_file, output_csv_file, server_ip, server_port, ip_to_device_name)


def get_device_name_from_ip(ip_address, json_file):
    try:
        # Load JSON data from file
        with open(json_file, 'r') as file:
            data = json.load(file)
        
        # Iterate through device configurations to find the matching IP address
        for device in data['deviceConfigurations']:
            if device['deviceIPAddress'] == ip_address:
                return device['deviceName']
        
        # If no match found
        return None
    
    except FileNotFoundError:
        print(f"Error: The file {json_file} does not exist.")
    except json.JSONDecodeError:
        print(f"Error: The file {json_file} contains invalid JSON.")
    except KeyError as e:
        print(f"Error: Missing expected key {e} in JSON data.")

# def nG1_device_interface(device_name, server_ip, server_port):
#     cookies = {f'NSSESSIONID':'vluxoT80NIg+Rq6rFewiFC/36XvUnnb26K6LK3lcGGw4h+ms/bXXxmbxVrY4g0u/kz8Vyt2fOeBf/QaQjCAeXUhTagCczdSuafHuF+wTojDjtMxO156KXZ1BV8w5FV7N'}
#     headers = {
#         'Content-Type': 'application/json',
#     }
#     response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{device_name}/interfaces', cookies=cookies, headers=headers, verify=False)
#     if response.status_code == 200:
#         print(device_name)
#         print(response.text)
#         with open('device-interface.json', 'w') as f:
#             f.write(response.text)
#     else:
#         logger.critical(response.text)

def nG1_device_interface(device_name, server_ip, server_port):
    cookies = {
        'NSSESSIONID': 'vluxoT80NIg+Rq6rFewiFC/36XvUnnb26K6LK3lcGGw4h+ms/bXXxmbxVrY4g0u/kz8Vyt2fOeBf/QaQjCAeXUhTagCczdSuafHuF+wTojDjtMxO156KXZ1BV8w5FV7N'
    }
    headers = {
        'Content-Type': 'application/json',
    }
    try:
        response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/{device_name}/interfaces', cookies=cookies, headers=headers, verify=False)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()  # Return the JSON response
#        logger.info(response.json())
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def update_csv_with_interface_name(csv_file, output_file, server_ip, server_port, ip_to_device_name):
    # Read the CSV file and group rows by ipAddress to minimize the number of API requests.
    device_rows = {}
    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            ip_address = row['ipAddress']
            if ip_address not in device_rows:
                device_rows[ip_address] = []
            device_rows[ip_address].append(row)

    # Fetch interface data for each unique ipAddress and update rows
    for ip_address, rows in device_rows.items():
        logger.info(f"Processing IP address: {ip_address}")
        device_name = ip_to_device_name.get(ip_address)  # Get the device name from the dictionary
        if not device_name:
            print(f"No device name found for IP address: {ip_address}. Skipping...")
            continue

        interface_info = nG1_device_interface(device_name, server_ip, server_port)
        if interface_info:
            # Create a dictionary for fast lookups
            interface_dict = {iface['interfaceNumber']: iface['interfaceName'] for iface in interface_info.get('interfaceConfigurations', [])}

            for row in rows:
                ifn = int(row['ifn'])
                # Update the row with the interfaceName
                row['interfaceName'] = interface_dict.get(ifn, 'Unknown Interface')
                row['deviceName'] = device_name  # Add the device name to the row

    # Write the updated data back to a new CSV file
    with open(output_file, mode='w', newline='') as file:
        fieldnames = ['deviceName','ipAddress', 'ifn', 'interfaceName', 'vitalStats_drops']
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        for rows in device_rows.values():
            csv_writer.writerows(rows)

#logging function
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }
    def format(self, record):
        formatter1 = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_fmt = formatter1
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def create_logging_function(log_filename):
    isExist = os.path.exists(log_dir)
    if not isExist:
       os.makedirs(log_dir)
#    log_save()
    LOG_LEVEL = logging.DEBUG
    LOGFORMAT = "  %(log_color)s%(asctime)s - %(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    from colorlog import ColoredFormatter
    logging.root.setLevel(LOG_LEVEL)
    formatter = ColoredFormatter(LOGFORMAT)
    stream = logging.StreamHandler()
    stream.setLevel(LOG_LEVEL)
    stream.setFormatter(formatter)
    logger = logging.getLogger('Restapi Log for Vitalsigns dropped packets')
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(stream)
    return logger

def rest_close(server_ip,server_port):
    #using curl to close api session
    logger.info('Closing API session cookie')
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
    logger.info('Response Status Code:', response.status_code)
    logger.info('Completed, removing session cookie')
    os.system('rm cookie.txt')

def final_output(int_file):
    # Step 1: Read the CSV file into a DataFrame
    input_file = int_file  # Change this to your input file name
    df = pd.read_csv(input_file)
    # Step 2: Filter rows where 'vitalStats_packets' is greater than zero
    filtered_df = df[df['vitalStats_packets'] > 0].copy()
    # Step 3: Rename the column 'vitalStats_packets' to 'vitalStats_drops'
    filtered_df.rename(columns={'vitalStats_packets': 'vitalStats_drops'}, inplace=True)
    # Step 4: Select the desired columns
    # Assuming the column names exactly match those provided in the example
    selected_columns = ['ipAddress', 'ifn', 'vitalStats_drops']
    filtered_df = filtered_df[selected_columns]
    # Step 4: Write the filtered and selected DataFrame to a new CSV file
    output_file = 'filtered_output.csv'  # Change this to your desired output file name
    filtered_df.to_csv(output_file, index=False)
    logger.info(f"Filtered data has been written to {output_file}")

def curl_api_open(nId,server_ip,server_port):
    logger.info('Making API call to nG1 RESTAPI')
    # Request headers
    headers = { 'Content-Type': 'application/xml'
    }
    # Request data (if needed)
    # Cookie (if needed)
    cookies = { 'NSSESSIONID': nId
    }
    # Perform POST request
    response = requests.post('https://'+server_ip+':'+server_port+url_open, headers=headers, cookies=cookies, verify=False)
    logger.info('Response Status Code:', response.status_code)
    logger.info('Response Content:', response.text)
    logger.info('Completed RESTAPI nG1 Call')
    # Save cookies to file if needed
    with open('cookie.txt', 'w') as f:
        for cookie in response.cookies:
           f.write(str(cookie.name) + '=' + str(cookie.value) + '\n')

def config_files():
    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read('.config.yaml')
    # server connection details
    nid = config.get('settings', 'nId')
    server_ip = config.get('settings', 'server_ip')
    server_port = config.getint('settings', 'server_port')
    return nid , server_ip, server_port

def xml_file_creation(output_folder,xml_file1):
    logger.info('Creating network service xml file for extracting dropped packets')
    xml_file = open(xml_file1,"wb")
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
#    clientColumn5 = ElementTree.SubElement(selectcolumn, "ClientColumn")
#    clientColumn6 = ElementTree.SubElement(selectcolumn, "ClientColumn")
#    clientColumn7 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    flowfilter = ElementTree.SubElement(root, "FlowFilterList")
    flowfil = ElementTree.SubElement(flowfilter, "FlowFilter")
    filter = ElementTree.SubElement(flowfil, "FilterList")
    flownet = ElementTree.SubElement(filter, "networkServiceId")
    flowint = ElementTree.SubElement(filter, "appId")
#    filter = ElementTree.SubElement(flowfil, "FilterList")
    functionlist = ElementTree.SubElement(root, "FunctionList")
#    function = ElementTree.SubElement(functionlist, "Function")
#    fname =  ElementTree.SubElement(function, "name")
#    fcolumn = ElementTree.SubElement(function, "column")
#    fnvalue = ElementTree.SubElement(function, "nValue")
#    forder = ElementTree.SubElement(function, "order")
#    fagg = ElementTree.SubElement(function, "aggrregateOther")
#    function1 = ElementTree.SubElement(functionlist, "Function")
#    f1name = ElementTree.SubElement(function1, "name")
#    f1column = ElementTree.SubElement(function1, "column")
    timedef = ElementTree.SubElement(root, "TimeDef")
    starttime = ElementTree.SubElement(timedef, "startTime")
    endtime = ElementTree.SubElement(timedef, "endTime")
    resolution = ElementTree.SubElement(timedef, "resolution")
#    this puts data in the xml tree for request
    networkparm.text = 'APPLICATION'
    clientColumn.text = 'appId'
    clientColumn1.text = 'ifn'
    clientColumn2.text = 'ipAddress'
    clientColumn3.text = 'vitalStatsFlag'
    clientColumn4.text = 'vitalStats_packets'
#    clientColumn5.text = 'synAck'
#    clientColumn6.text = 'synRetry'
#    clientColumn7.text = 'targetTime'
#    ='All Locations'
#    inf_num='184549384'
    flownet.text = '61499420'
    flowint.text = '184549384'
#    fname.text = "TopN"
    starttime.text = '2024-8-21_9:40:00'
#    starttime.text = start_time
#    endtime.text = end_time
    endtime.text = '2024-8-21_10:40:00'
    resolution.text = 'NO_RESOLUTION'
    tree = ElementTree.ElementTree(root)
    #  testing of the xml file - pretty format
    #print(etree..tostring(root, pretty_print=True))
    # writes Production xml file
    tree.write(xml_file, xml_declaration=True)

logger = create_logging_function(log_filename)
nid , server_ip, server_port = config_files() 
create_dirs()
xml_file_creation(xml_dir,xml_file)
#curl_command(nid, server_ip, server_port)
nG1_call_drops(server_ip, server_port, xml_file, 'vitalsigns_drp_pkts.csv')
#nG1_device_interface('172.23.246.108', server_ip, server_port)
logger.info("all Files will be sorted under the following folder: "+output_folder)
