#!/usr/bin/env python3

#Script was Writtent by NetScout Premium Servicess
#Author James Vigliotti

#These classes/modules needed to run script
import pandas as pd
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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
#import xml.etree.ElementTree as ET
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
xml_file =xml_dir+'/pkt_drop_ntksvc.xml'
server_data = folder+'/server_data'
log_dir = folder+'/log'
log_filename = log_dir+'/restapi_vital_drp_pkts.log'
working_folder = output_folder+'/working'
results_folder = folder+'/results'

__version__ = '1.2'


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
    new_dir(working_folder)
    new_dir(server_data)
    new_dir(results_folder)


def nG1_call_drops(name_file, nId, server_ip, server_port, xml_in_file, xml_output_file):
      # Suppress the warning
    warnings.simplefilter('ignore', InsecureRequestWarning)
    cookies = {'NSSESSIONID':'{}'.format(nId)}
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
        final_output(working_folder+'/vitalsigns_drp_pkts.csv')
        nG1_call_get_devices(nid, server_ip, server_port)
        add_device_name(nid, name_file, working_folder+'/filtered_output.csv', server_ip, server_port)
        
    else:
        logger.critical(response.text)

def nG1_call_get_devices(nId, server_ip, server_port):
    cookies = {'NSSESSIONID':'{}'.format(nId)}
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.get(f'https://{server_ip}:{server_port}/ng1api/ncm/devices/', cookies=cookies, headers=headers, verify=False)
    if response.status_code == 200:
        with open(working_folder+'/device-list.json', 'wb') as f:
            f.write(response.content)
    else:
        logger.critical(response.text)

def add_device_name(nid, name_file, i_file, server_ip, server_port):
    input_file = i_file  # The input CSV file name
    df = pd.read_csv(input_file)
    json_file = working_folder+'/device-list.json'  # The JSON file path containing device configurations
    output_csv_file = f'{results_folder}/ISNG_drops_{name_file}.csv'

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
    update_csv_with_interface_name(input_file, output_csv_file, nid, server_ip, server_port, ip_to_device_name)


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

def nG1_device_interface(device_name, nId, server_ip, server_port):
    cookies = {'NSSESSIONID':'{}'.format(nId)}
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

def update_csv_with_interface_name(csv_file, output_file, nid, server_ip, server_port, ip_to_device_name):
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

        interface_info = nG1_device_interface(device_name, nid, server_ip, server_port)
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
        fieldnames = ['deviceName','ipAddress', 'ifn', 'interfaceName', 'drops']
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        for rows in device_rows.values():
            csv_writer.writerows(rows)
    # write output file xlsx
    df = pd.read_csv(output_file)
    excel_file = f'{results_folder}/ISNG_drops_{name_file}.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
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
    # Set up file logging
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-8s | %(message)s'))
    logger.addHandler(file_handler)
    return logger

def get_user_input():
    """Function to get user input for server_ip."""
    server_ip = input("Enter DGM IP or standalone: ")
    server_port = input("Enter server port: ")
    nId = input("Enter nG1 Token from user management: ")
    return server_ip, server_port, nId

def write_config_file(server_ip, server_port, nId):
    """Function to write the configuration to a file."""
    config_content = f"""[settings]
server_ip = {server_ip}
server_port = {server_port}
nId = {nId}

[api_call]

network_service = All locations

[time]
#this set the days ,hours, months to pull data
time_f = days
#this is set for example 1 hour ,1 day or 1 month
n_days = 7
"""
    
    # Specify the file path
    output_file_path = server_data+'/.config.yaml'

    # Write the configuration to the file
    with open(output_file_path, 'w') as file:
        file.write(config_content)



def final_output(int_file):
    # Step 1: Read the CSV file into a DataFrame
    input_file = int_file  # Change this to your input file name
    df = pd.read_csv(input_file)
    # Step 2: Filter rows where 'vitalStats_packets' is greater than zero
    filtered_df = df[df['vitalStats_packets'] > 0].copy()
    # Step 3: Rename the column 'vitalStats_packets' to 'vitalStats_drops'
    filtered_df.rename(columns={'vitalStats_packets': 'drops'}, inplace=True)
    # Step 4: Select the desired columns
    # Assuming the column names exactly match those provided in the example
    selected_columns = ['ipAddress', 'ifn', 'drops']
    filtered_df = filtered_df[selected_columns]
    # Step 4: Write the filtered and selected DataFrame to a new CSV file
    output_file = working_folder+'/filtered_output.csv'  # Change this to your desired output file name
    filtered_df.to_csv(output_file, index=False)
    logger.info(f"Filtered data has been written to {output_file}")

def config_files():
    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read(server_data+'/.config.yaml')
    # server connection details
    nid = config.get('settings', 'nId')
    server_ip = config.get('settings', 'server_ip')
    server_port = config.get('settings', 'server_port')
    time_f =  config.get('time', 'time_f')
    n_days =  config.getint('time', 'n_days')
    ntk_svc = config.get('api_call', 'network_service')
    return nid , server_ip, server_port, time_f, n_days, ntk_svc 

def sevice_id(xml_string): # Parse the XML string
    root = ET.fromstring(xml_string)
    # Find the <id> element
    id_element = root.find('.//id')

    # Extract and print the text content
    if id_element is not None:
        service_id = id_element.text
        logger.info(f"Service ID: {service_id}")
    else:
        logging.info("ID element not found.")
    return service_id

def nG1_call_service_id(nId , server_ip, server_port, ntk_svc):
    url_open = f'/ng1api/ncm/services/{ntk_svc}'
    # Suppress the warning
    warnings.simplefilter('ignore', InsecureRequestWarning)
    # Request headers
    headers = { 'Content-Type': 'application/xml'
    }
    # Request data (if needed)
    # Cookie (if needed)
    cookies = { 'NSSESSIONID': nId
    }
    # Perform POST request
    response = requests.get('https://'+server_ip+':'+server_port+url_open, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 200:
        xml_string = response.content
        service_id = sevice_id(xml_string)
    else:
        print(response.text)
    return service_id

def xml_file_creation(ntk_svc,output_folder,xml_file1,time_f,n_days):
    #converted  network service to service_id
    nid , server_ip, server_port, time_f, n_days, ntk_svc = config_files()
    s_id = nG1_call_service_id(nid , server_ip, server_port, ntk_svc)
    logger.info('Creating network service xml file for extracting dropped packets')
    # Get the current time
    current_time = datetime.now()

    # Round down the minute part to the nearest multiple of 5 for both start and end times
    rounded_minutes = current_time.minute - (current_time.minute % 5)
    #time delta 
    if time_f == 'hours':
        time_delta = timedelta(hours=n_days)
    elif time_f ==  'days':
        time_delta = timedelta(days=n_days)
    elif time_f == 'months':
        time_delta = relativedelta(months=n_days)
    # Create new datetime objects with the rounded minutes
#    rounded_start_time = current_time.replace(minute=rounded_minutes) - timedelta(time_f = n_days) #31 days.
    rounded_start_time = current_time.replace(minute=rounded_minutes) - time_delta
    rounded_end_time = current_time.replace(minute=rounded_minutes)

    if time_f == 'months' or time_f == 'days':
        time_difference = rounded_end_time - rounded_start_time
        time_days = time_difference.days
        logger.info(f'Time difference: {time_days} {time_f}')
        name_file = f'last_{time_days}_days'
    else:
        time_difference = rounded_end_time - rounded_start_time
        time_difference_str = str(time_difference)
        stripped_time_difference = time_difference_str.split(':')[0].strip()
        logger.info(f'Time difference: {stripped_time_difference} {time_f}')
        name_file = f'last_{stripped_time_difference}_hour'

    # Format the start and end times as needed
    start = rounded_start_time.strftime("%Y-%m-%d_%H:%M:%S")
    logger.info(f'Start time for getting packets: {start}')
    end = rounded_end_time.strftime("%Y-%m-%d_%H:%M:%S")
    logger.info(f'End time for getting packets: {end}')
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
    flowfilter = ElementTree.SubElement(root, "FlowFilterList")
    flowfil = ElementTree.SubElement(flowfilter, "FlowFilter")
    filter = ElementTree.SubElement(flowfil, "FilterList")
    flownet = ElementTree.SubElement(filter, "networkServiceId")
    flowint = ElementTree.SubElement(filter, "appId")
    functionlist = ElementTree.SubElement(root, "FunctionList")
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
    flownet.text = s_id
    flowint.text = '184549384'
    starttime.text = start
    endtime.text = end
    resolution.text = 'NO_RESOLUTION'
    tree = ElementTree.ElementTree(root)
    #  testing of the xml file - pretty format
    #print(etree..tostring(root, pretty_print=True))
    # writes Production xml file
    tree.write(xml_file, xml_declaration=True)
    return name_file

logger = create_logging_function(log_filename)
# Run the date command and capture its output
process = subprocess.Popen(['date'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()

# Decode the output from bytes to string and strip any trailing newlines
date_run = stdout.decode().strip()

logger.info(f' run date of Script :{date_run}')
logger.info(f"Running script version {__version__}")
create_dirs()

if platform.system() =='Windows':
    p_version = sys.version
    p_os = platform.platform()
    logger.info('Script is running on '+p_os+' running python version '+p_version)
else:
    p_version = sys.version
    p_os = distro.name()
    p_dver = distro.version()
    logger.info('Script is running on '+p_os+' '+p_dver+' running python version '+p_version)
#create config.yaml file
if os.path.isfile(server_data+'/.config.yaml'):
    logger.info(f"The file config file exists.")
else:
    server_ip,server_port, nId = get_user_input()
    write_config_file(server_ip, server_port, nId)

nid , server_ip, server_port, time_f, n_days, ntk_svc = config_files() 
name_file = xml_file_creation(ntk_svc, output_folder,xml_file,time_f,n_days)
nG1_call_drops(name_file, nid, server_ip, server_port, xml_file, working_folder+'/vitalsigns_drp_pkts.csv')
logger.info("Results for ISNG drops will be under the following folder: "+results_folder)
