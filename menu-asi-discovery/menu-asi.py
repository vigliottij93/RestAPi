#!/usr/bin/env python3

#Script was Writtent by NetScout Premium Servicess
#Author James Vigliotti

#These classes/modules needed to run script
import pandas as pd
import json
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
import configparser
from pathlib import Path
import paramiko
import time
import subprocess
from cryptography.fernet import Fernet
import logging
from colorama import Fore, Style, init
import tarfile
from datetime import datetime

folder_main = 'restapi_url_discovery'
working_dir = folder_main+'/working_files'
result_fldr = folder_main+'/results'
server_data = folder_main+'/server_data'
log_dir = folder_main+'/logs'
log_filename = log_dir+'/url_discovery.log'

url_open = '/ng1api/rest-sessions'
url_close = '/ng1api/rest-sessions/close'

def show_menu():
    print("===== Menu =====")
    print("1. decrypt config file for editing")
    print("2. Get url discovery")
    print("3. All Discovered Web Applications(DPC)")
    print("4. ASI Discovered Ports")
    print("5. TBD")
    print("6. TBD")
    print("7. TBD")
    print("10. Exit")
    print("================")

def new_dir(folder_name):
    path = os.path.join(".", folder_name)
    try:
        os.mkdir(path)
        logger.info(f"Directory '{folder_name}' created.")
#        logger.info(f"Directory '{folder_name}' created.")
    except FileExistsError:
        logger.info(f"Directory '{folder_name}' already exists.")
       # logger.info(f"Directory '{folder_name}' already exists.")

def create_dirs(folder_n, working_fldr, results_fldr, server_data, log_dir):
    new_dir(folder_n)
    new_dir(working_fldr)
    new_dir(results_fldr)
    new_dir(server_data)
    new_dir(log_dir)

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
#    log_dir = os.path.dirname(log_filename)
#    isExist = os.path.exists(log_filename)
#    if not isExist:
#       os.makedirs(log_filename)
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

#used for encrypt and decrypt
def gen_encrypt_key():
    """Generate a key and save it to a file."""
    key = Fernet.generate_key()
    with open(server_data+'/encryption_key.key', 'wb') as key_file:
        key_file.write(key)

def load_key():
    """Load the encryption key from a file."""
    try:
        with open(server_data+'/encryption_key.key', 'rb') as key_file:
            key = key_file.read()
        return Fernet(key)
    except FileNotFoundError:
        logger.critical("Key file not found. Please generate a key first.")
        raise

def encrypt_file(file_path):
    """Encrypt a file using the loaded key."""
    cipher_suite = load_key()  # Load the key

    temp_file_path = file_path + '.tmp'

    try:
        # Read the original file's data
        with open(file_path, 'rb') as file:
            file_data = file.read()

        # Encrypt the data
        encrypted_data = cipher_suite.encrypt(file_data)

        # Write the encrypted data to a temporary file
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(encrypted_data)

        # Replace the original file with the temporary file
        os.replace(temp_file_path, file_path)
    except Exception as e:
        logger.critical(f"An error occurred during encryption: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    file_name = server_data+'/.encrypt.txt'
    content = 'file was encrypted.'

    # Open the file in write mode ('w'). If the file doesn't exist, it will be created.
    with open(file_name, 'w') as file:
        # Write the content to the file
        file.write(content)

def decrypt_file(file_path):
    """Decrypt a file using the loaded key."""
    cipher_suite = load_key()  # Load the key
    fname = server_data+'/.encrypt.txt'
    temp_file_path = file_path + '.tmp'

    try:
        # Read the encrypted file's data
        with open(file_path, 'rb') as file:
            encrypted_data = file.read()

        # Decrypt the data
        decrypted_data = cipher_suite.decrypt(encrypted_data)

        # Write the decrypted data to a temporary file
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(decrypted_data)

        # Replace the encrypted file with the temporary file
        os.replace(temp_file_path, file_path)
        if os.path.exists(fname):
            os.remove(fname)
    except Exception as e:
        logger.critical(f"An error occurred during decryption: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def config_files():
    # Read configuration from config.ini
    config = configparser.ConfigParser()
    config.read('.config.ini')
    # server connection details
    nid = config.get('server', 'nId')
    server_ip = config.get('server', 'server_ip')
    server_port = config.get('server', 'server_port')
    uriRESTapiDevice = config.get('urls', 'uriRESTapiDevice')
    #time for report
    dur_time = config.get('time', 'duration')
    text_edit = config.get('texteditor', 'text_edit')
    return  nid, server_ip, server_port, uriRESTapiDevice , dur_time, text_edit

def curl_api_open(nId,server_ip,server_port,working_fldr):
    logger.info('Making API call to nG1 RESTAPI')
    # Request headers
    headers = { 'Content-Type': 'application/xml'
    }
    # Request data (if needed)
    # Disable urllib3 warnings about insecure HTTPS requests
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # Cookie (if needed)
    cookies = { 'NSSESSIONID': nId
    }
    # Perform POST request
    response = requests.post('https://'+server_ip+':'+server_port+url_open, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 200 :
#        print(response.status_code)
        logger.info('Response Content: Sucessful')
        logger.info('Completed RESTAPI nG1 Call')
        # Save cookies to file if needed
        with open(working_fldr+'/cookie.txt', 'w') as f:
            for cookie in response.cookies:
                f.write(str(cookie.name) + '=' + str(cookie.value) + '\n')
    else:
        logger.critical(response.text) 

def rest_close(server_ip,server_port,working_fldr):
    #using curl to close api session
    # Disable urllib3 warnings about insecure HTTPS requests
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logger.info('Closing API session cookie')
    # Cookie file path
    cookie_file = f'{working_fldr}/cookie.txt'
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
    if response.status_code == 200:
        logger.info('Closed api session successful')
        logger.info('Completed, removing session cookie')
        os.system(f'rm {working_fldr}/cookie.txt')
    else:
        logger.critical(response.text)

def nG1_call_url_get(server_ip,server_port,uriRESTapiDevice,dur_time,working_dir):
    # Disable urllib3 warnings about insecure HTTPS requests
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logger.info('Requestiong discovered URLs from nG1')
    # Request headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Cookie file path
    cookie_file = f'{working_dir}/cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
    # Perform GET request
    response = requests.get('https://'+server_ip+':'+server_port+uriRESTapiDevice+'?duration='+dur_time, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:
        with open(working_dir+'/nG1_discovery_url-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open(working_dir+'/nG1_discovery_url.json', 'wb') as r_write:
            r_write.write(response.content)
        data = response.json()
        # Convert JSON to DataFrame
        # Extract the 'DiscoveredPorts' data
        discovered_urls = data.get('DiscoveredURLs', [])
        # Check if the list is not empty
        if discovered_urls:
            # Convert the data to a DataFrame
            df = pd.DataFrame(discovered_urls)
            # Export DataFrame to CSV
            df.to_csv(f'{result_fldr}/web_urls.csv', index=False)
            # Export DataFrame to XLS (Excel)
            df.to_excel(f'{result_fldr}/web_urls.xlsx', index=False, engine='openpyxl')
        else:
            logger.info("No data available. No files written.")
    logger.info('Finished url list from nG1')

def is_valid_json(data, required_key):
    """Check if the JSON data contains the required key and that the key holds a non-empty list."""
    logger.info(required_key)
    return required_key in data and isinstance(data[required_key], list) and len(data[required_key]) > 0

def nG1_web_app_disc(server_ip,server_port,dur_time,working_dir):
    web_uri = f'/ng1api/ncm/asitrafficdiscovery/webapplications?duration={dur_time}'
    # Disable urllib3 warnings about insecure HTTPS requests
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logger.info('Requestiong discovered URLs from nG1')
    # Request headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Cookie file path
    cookie_file = f'{working_dir}/cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
    # Perform GET request
    response = requests.get('https://'+server_ip+':'+server_port+web_uri, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:
        with open(working_dir+'/nG1_dpc_app-discover_url-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open(working_dir+'/nG1_dpc_app_discovery.json', 'wb') as r_write:
            r_write.write(response.content)
#        if 'application/json' in response.headers.get('Content-Type', ''):
            # Parse the JSON data
        if response.text != "Web applications are not enabled":
            data = response.json()
            required_key = 'DiscoveredURLs'
            if is_valid_json(data, required_key):
                discovered_ports = data.get('DiscoveredURLs', [])
                # Check if the list is not empty
                if discovered_ports:
                    # Convert the data to a DataFrame
                    df = pd.DataFrame(discovered_ports)
                    # Export DataFrame to CSV
                    df.to_csv(f'{result_fldr}/DPC_web_applications.csv', index=False)
                    # Export DataFrame to XLS (Excel)
                    df.to_excel(f'{result_fldr}/DPC_web_applications.xlsx', index=False, engine='openpyxl')
                else:
                    logger.info(f"{response.json()} . No files written.")
        else:
            logger.critical(f'{response.text}.') 
    logger.info('Finished url list from nG1')

def nG1_asi_port_disc(server_ip,server_port,dur_time,working_dir,result_fldr):
    web_uri = f'/ng1api/ncm/asitrafficdiscovery/port?duration={dur_time}'
    # Disable urllib3 warnings about insecure HTTPS requests
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logger.info('Requestiong ASI discovered ports from nG1')
    # Request headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Cookie file path
    cookie_file = f'{working_dir}/cookie.txt'
    # Load cookies from file
    cookies = {}
    with open(cookie_file, 'r') as f:
        for line in f.read().split(';'):
            if '=' in line:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
    # Perform GET request
    response = requests.get('https://'+server_ip+':'+server_port+web_uri, headers=headers, cookies=cookies, verify=False)
    if response.status_code == 404 or response.status_code == 500:
        with open(working_dir+'/nG1_asi-discovered_ports-error.json', 'wb') as f:
            f.write(response.content)
    else:
        with open(working_dir+'/nG1_asi-discovered_ports.xml', 'wb') as r_write:
            r_write.write(response.content)
        
        data = response.json()
        # Convert JSON to DataFrame
        discovered_ports = data.get('DiscoveredPorts', [])
        # Check if the list is not empty
        if discovered_ports:
            # Convert the data to a DataFrame
            df = pd.DataFrame(discovered_ports)
            # Export DataFrame to CSV
            df.to_csv(f'{result_fldr}/discovered_ports.csv', index=False)
            # Export DataFrame to XLS (Excel)
            df.to_excel(f'{result_fldr}/discovered_ports.xlsx', index=False, engine='openpyxl')
        else:
            logger.info("No data available. No files written.")
    logger.info('Finished ASI port Discovery list from nG1')

def open_file_in_editor(file_path,text_edit):
    # Open the file in nano editor
    subprocess.run([text_edit, file_path], check=True)
 
logger = create_logging_function(log_filename)
# Run the date command and capture its output
process = subprocess.Popen(['date'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()

# Decode the output from bytes to string and strip any trailing newlines
date_run = stdout.decode().strip()

logger.info(f' run date of Script :{date_run}')
def main():
    file_to_encrypt = '.config.ini'
    create_dirs(folder_main, working_dir, result_fldr, server_data, log_dir)
    # Check if the key file exists; if not, generate it
    if not os.path.exists(server_data+'/encryption_key.key'):
        gen_encrypt_key()  # Generate and save the key

    # Encrypt the file
    if not os.path.exists(server_data+'/.encrypt.txt'):
        encrypt_file(file_to_encrypt)
        logger.info(f'File {file_to_encrypt} has been encrypted.')
    if platform.system() =='Windows':
        p_version = sys.version
        p_os = platform.platform()
        logger.info('Script is running on '+p_os+' running python version '+p_version)
    else:
        p_version = sys.version
        p_os = distro.name()
        p_dver = distro.version()
        logger.info('Script is running on '+p_os+' '+p_dver+' running python version '+p_version)
    while True:
        show_menu()
        choice = input("Enter your choice (1-10): ")
        if choice == '1':
            logger.info('Getting  server configuration data')
            # get Server data
            # Decrypt the file
            file_to_encrypt = '.config.ini'
            decrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been decrypted and saved with the same name.')
            nid, server_ip, server_port, uriRESTapiDevice, dur_time, text_edit = config_files()
            open_file_in_editor(file_to_encrypt,text_edit)
            encrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been encrypted.')

        elif choice == '2':
            file_to_encrypt = '.config.ini'
            decrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been decrypted and saved with the same name.')
            logger.info('Getting  server configuration data')
            nid, server_ip, server_port, uriRESTapiDevice, dur_time, text_edit = config_files()
            curl_api_open(nid,server_ip,server_port,working_dir)
#            logger.info(f'{nid}, {server_ip}, {server_port}, {uriRESTapiDevice}')
            encrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been encrypted.')
            logger.info(f'Making nG1 call for url discovery for {dur_time}')
            nG1_call_url_get(server_ip,server_port,uriRESTapiDevice,dur_time,working_dir)
            rest_close(server_ip,server_port,working_dir)
        elif choice == '3':
            file_to_encrypt = '.config.ini'
            decrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been decrypted and saved with the same name.')
            logger.info('Getting  server configuration data')
            nid, server_ip, server_port, uriRESTapiDevice, dur_time, text_edit = config_files()
            curl_api_open(nid,server_ip,server_port,working_dir)
#            logger.info(f'{nid}, {server_ip}, {server_port}, {uriRESTapiDevice}')
            encrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been encrypted.')
            logger.info(f'Making nG1 call for DPC application discovery for {dur_time}')
            nG1_web_app_disc(server_ip,server_port,dur_time,working_dir)
            rest_close(server_ip,server_port,working_dir)
            logger.info(f'Completed nG1 call for DPC application discovery for {dur_time}')
        elif choice == '4':
            file_to_encrypt = '.config.ini'
            decrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been decrypted and saved with the same name.')
            logger.info('Getting  server configuration data')
            nid, server_ip, server_port, uriRESTapiDevice, dur_time, text_edit = config_files()
            curl_api_open(nid,server_ip,server_port,working_dir)
#            logger.info(f'{nid}, {server_ip}, {server_port}, {uriRESTapiDevice}')
            encrypt_file(file_to_encrypt)
            logger.info(f'File {file_to_encrypt} has been encrypted.')
            logger.info(f'Making nG1 call for ASI discovery for {dur_time}')
            nG1_asi_port_disc(server_ip,server_port,dur_time,working_dir,result_fldr)
            rest_close(server_ip,server_port,working_dir)
            logger.info(f'Completed nG1 call for ASI port  discovery for {dur_time}')
        elif choice == '10':
            logger.info("Exiting the program. Goodbye!")
            break
        else:
            logger.info("Invalid choice. Please enter a number from menu.")
if __name__ == "__main__":
    main()