#!/usr/bin/env python3
#importing the module

import csv
import requests
import os
import touch
import glob
import getpass
from cryptography.fernet import Fernet
import pathlib
from datetime import datetime, timedelta
import logging
import touch
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import time
import pandas as pd
from halo import Halo
import xml.etree.ElementTree as ET
import pandas as pd

folder_name = 'nG1_restapi'
day = datetime.now().strftime("%A")
folder_time = datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p")
server_data = 'server_data'
server_config = folder_name+'/'+server_data+'/serverconfig.txt'
server_key = folder_name+'/'+server_data+'/serverkey.key'
log_name = folder_name+'/activity.log'
good = 'nG1-activity_good.xml'
bad = 'nG1-activity_bad.xml'
good_raw = 'nG1-activity_good-raw.xml'
xml_file = folder_name+'/'+good_raw

isExist = os.path.exists(folder_name)
if not isExist:
    # Create a new directory because it does not exist
    os.makedirs(folder_name)

log_file_exist = os.path.isfile(log_name)
if not log_file_exist:
    touch.touch(log_name)


logging.basicConfig(filename=log_name,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def makekey_nG1():
    isExist = os.path.exists(folder_name+'/'+server_data)
    if not isExist:
    # Create a new directory because it does not exist
        os.makedirs(folder_name+'/'+server_data)
    # key generation
#    print("Generating Key for encryption.")
    logging.info("Generating Key for Server configuration encryption.")
    key = Fernet.generate_key()
    logging.info("Writing new Server key to file.")
    # string the key in a file
    with open(server_key, 'wb') as filekey:
        filekey.write(key)

def encryptfile(filename,keyfile):
    # opening the key
#    logging.info("Encrypting server configuration file!")
    with open(keyfile, 'rb') as filekey:
        key = filekey.read()
    # using the generated key
    fernet = Fernet(key)
    # opening the original file to encrypt
    with open(filename, 'rb') as file:
        original = file.read()
    # encrypting the file
    encrypted = fernet.encrypt(original)
    # opening the file in write mode and
    # writing the encrypted data
    with open(filename, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
#    logging.info("Encryption completed!")

def existKey_nG1(filename,file_key):
    #checks for the  output directory
    file = pathlib.Path(file_key)
    if not file.exists ():
        makekey_nG1()
        fd = open(filename,"w")
        user_input = input("Please enter DGM/Standalone IP address: ")
        user_input1 = input("Please enter Server Port: ")
        user_input2 = getpass.getpass("Please NetScout Authentication Token: ")
        fd.write(user_input+','+user_input1+','+user_input2)
        fd.close()
        logging.info("Server configuration complete")
        encryptfile(server_config,server_key)
    else:
        logging.info('Configuration file already been run')


def decrpytfile(filename,keyfile):
    # using the key
    # opening the key
    with open(keyfile, 'rb') as filekey:
        key = filekey.read()
    fernet = Fernet(key)
    # opening the encrypted file
    with open(filename, 'rb') as enc_file:
        encrypted = enc_file.read()
    # decrypting the file
    decrypted = fernet.decrypt(encrypted)
    # opening the file in write mode and
    # writing the decrypted data
    with open(filename, 'wb') as dec_file:
        dec_file.write(decrypted)

def indent(elem, level=0):
   # Add indentation
   indent_size = "  "
   i = "\n" + level * indent_size
   if len(elem):
      if not elem.text or not elem.text.strip():
         elem.text = i + indent_size
      if not elem.tail or not elem.tail.strip():
         elem.tail = i
      for elem in elem:
         indent(elem, level + 1)
      if not elem.tail or not elem.tail.strip():
         elem.tail = i

def pretty_print_xml_elementtree(xml_string):
   good = 'nG1_success_health.txt'
   # Parse the XML string
   root = ET.fromstring(xml_string)
   # Indent the XML
   indent(root)
   # Convert the XML element back to a string
   pretty_xml = ET.tostring(root, encoding="unicode")
   # Print the pretty XML
#   print(pretty_xml)
   good_response = open(folder_name+'/'+good,"a")
   good_response.write(pretty_xml)
   good_response.close()

def get_isng_nG1_call():
    bad = 'nG1_upload_error.xml'
    #Polling DGM/Local for Device info
    requests.packages.urllib3.disable_warnings()
    cookies_dict = {"NSSESSIONID": nId}
    headers = {
        'Content-Type': 'application/xml',
    }
    response = requests.get('https://'+server_ip+':'+server_port+'/ng1api/ncm/activitylogs?duration_filter=Last 31 days' , headers=headers, verify=False, cookies=cookies_dict)
    # inline data read the  response from nG1 for  all Devices
    if response.status_code == 200:
        with open(folder_name+'/'+good, "w") as b_file:
            soup_good = BeautifulSoup(response.content, 'xml')  
            b_file.write(soup_good.prettify())
        with open(folder_name+'/'+good_raw, "wb") as g_file:
            g_file.write(response.content)
    else:
        with open(folder_name+'/'+bad, "w") as b1_file:
            soup1 = BeautifulSoup(response.content, 'xml')
            b1_file.write(soup1.prettify())

def user_info():
    # Parse the XML data from the file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Initialize lists to store extracted data
    usernames = []
    activities = []
    details = []
    timestamps = []

    # Iterate through each ActivityLog
    for activity_log in root.findall('.//ActivityLog'):
        username = activity_log.find('User').text
        activity = activity_log.find('Activity').text
        timestamp = activity_log.find('Time').text
        # Extract only the date portion (01/22/2024) from the timestamp
        date_part = timestamp.split(' ')[0]
        details_element = activity_log.find('Details')
        if details_element is not None:
            details_text = details_element.text
        else:
            details_text = "No details available"
        # Exclude 'system,jvigliotti' user from detailed information
        if username != 'SYSTEM' and username != 'JVIGLIOTTI' and activity.lower() not in ['user session removed', 'user logged out']:
            usernames.append(username)
            activities.append(activity)
            timestamps.append(date_part)  # Use date_part instead of full timestamp
            # Extract additional details
            #details.append(activity_log.find('Details').text)
            details.append(details_text)


    # Create a DataFrame with detailed information
    df_detailed = pd.DataFrame({'UserName': usernames, 'ActivityInfo': activities, 'Details': details, 'Date': timestamps})

    # Group by UserName, ActivityInfo, and Date, and count the occurrences for detailed information
    df_detailed_grouped = df_detailed.groupby(['UserName', 'ActivityInfo', 'Date']).size().reset_index(name='Count')

    # Group by ActivityInfo and Date, and sum the counts for summary
    df_summary = df_detailed_grouped.groupby(['ActivityInfo'])['Count'].sum().reset_index()
    # Extract Day/Date and count 'User logged in' activity for each day (excluding 'system' user)
    #df_activity_log = pd.DataFrame({'ActivityDate': df_detailed_grouped[(df_detailed_grouped['UserName'] != 'system') & (df_detailed_grouped['ActivityInfo'] == 'User logged in')]['Date'].unique(), 'ActiveUsers': df_detailed_grouped[(df_detailed_grouped['UserName'] != 'system') & (df_detailed_grouped['ActivityInfo'] == 'User logged in')].groupby('Date')['Count'].sum()})

    # Create the DataFrame with 'ActivityDate' as index and 'ActiveUsers' as values
    df_activity_log = pd.DataFrame({'ActiveUsers': df_detailed_grouped[(df_detailed_grouped['UserName'] != 'system') & (df_detailed_grouped['UserName'] != 'JVIGLIOTTI') & (df_detailed_grouped['ActivityInfo'] == 'User logged in')].groupby('Date')['Count'].sum()})

    # Reset the index and rename the index column to 'ActivityDate'
    df_activity_log.reset_index(inplace=True)
    df_activity_log.rename(columns={'Date': 'ActivityDate'}, inplace=True)
    # Print Day/Date and ActiveUsers
    #print(df_activity_log[['ActivityDate', 'ActiveUsers']])

    # Save to Excel file with three sheets
    with pd.ExcelWriter('activity_summary_detailed_log.xlsx', engine='xlsxwriter') as writer:
        # Write summary sheet (Sheet 1)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

        # Write detailed information sheet (Sheet 2)
        df_detailed_grouped.to_excel(writer, sheet_name='Detailed', index=False)

        # Write activity log sheet (Sheet 3)
        df_activity_log.to_excel(writer, sheet_name='Activity Log', index=False)

    print("Summary, detailed information, and activity log saved successfully.")
    logging.info("Summary, detailed information, and activity log saved successfully.")



existKey_nG1(server_config,server_key)
decrpytfile(server_config,server_key)
file_decrypt = open(server_config,"r")
for line in file_decrypt:
    #Let's split the line into an array called "fields" using the "," as a separator
    fields = line.split(",")
    #and let's extract the data:
    server_ip = fields[0]
    server_port = fields[1]
    nId = fields[2]
file_decrypt.close()
logging.info('Decrypted saved server configuration info')
encryptfile(server_config,server_key)
logging.info('Re-encrypted server configuration info')
#spinner.stop()
get_isng_nG1_call()

user_info()

