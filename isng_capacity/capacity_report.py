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
import pathlib

def xml_file(network_id):
  # Get the current time
    current_time = datetime.now()

    # Round down the minute part to the nearest multiple of 5 for both start and end times
    rounded_minutes = current_time.minute - (current_time.minute % 5)

    # Create new datetime objects with the rounded minutes
#    rounded_start_time = current_time.replace(minute=rounded_minutes) - timedelta(hours = 1) #Last hour.
    rounded_start_time = current_time.replace(minute=rounded_minutes) - timedelta(days = 31) #Last hour
    rounded_end_time = current_time.replace(minute=rounded_minutes)
    print(f'ISNG Capacity Report from {rounded_start_time} to {rounded_end_time}')
    # Format the start and end times as needed
    start = rounded_start_time.strftime("%Y-%m-%d_%H:%M:%S")
    end = rounded_end_time.strftime("%Y-%m-%d_%H:%M:%S")
    print('Creating network service xml file for extracting application list volume')
    xml_file = open('util.xml',"wb")

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
    clientColumn6 = ElementTree.SubElement(selectcolumn, "ClientColumn")
#    clientColumn7 = ElementTree.SubElement(selectcolumn, "ClientColumn")
    flowfilter = ElementTree.SubElement(root, "FlowFilterList")
    flowfil = ElementTree.SubElement(flowfilter, "FlowFilter")
    filter = ElementTree.SubElement(flowfil, "FilterList")
    flownet = ElementTree.SubElement(filter, "networkServiceId")
#    flowint = ElementTree.SubElement(filter, "srcAddress")
#    flowfil1 = ElementTree.SubElement(flowfilter, "FlowFilter")
#    filter2 = ElementTree.SubElement(flowfil1, "FilterList")
#    flownet2 = ElementTree.SubElement(filter2, "networkServiceId")
#    flowint2 = ElementTree.SubElement(filter2, "destAddress")
    functionlist = ElementTree.SubElement(root, "FunctionList")
    timedef = ElementTree.SubElement(root, "TimeDef")
    starttime = ElementTree.SubElement(timedef, "startTime")
    endtime = ElementTree.SubElement(timedef, "endTime")
    resolution = ElementTree.SubElement(timedef, "resolution")
#    duration = ElementTree.SubElement(timedef, "duration")
#    this puts data in the xml tree for request
    networkparm.text = 'APPLICATION'
    clientColumn.text = 'bitRate'
    clientColumn1.text = 'droppedPktCnt'
    clientColumn2.text = 'ifn'
    clientColumn3.text = 'ipAddress'
    clientColumn4.text = 'packetRate'
    clientColumn5.text = 'utilization'
    clientColumn6.text = 'targetTime'
#    clientColumn7.text = 'ifn'
    flownet.text = network_id
#    flowint.text = src_address
#    flownet2.text = '175852513'
#    flowint2.text = src_address
    starttime.text = start
    endtime.text = end
#    resolution.text = 'ONE_HOUR'
    resolution.text ='NO_RESOLUTION'
#    duration.text = 'LAST_HOUR'
    tree = ElementTree.ElementTree(root)
    # writes Production xml file
    tree.write(xml_file, xml_declaration=True)
    return rounded_start_time

def nG1_login_data():
    print('Gathering nG1 login data')
#    user_name = input('Please enter nG1 user id: ')
    server_ip = input('Please enter nG1 DGM/Standalone ip: ')
    server_port = input('Please enter the server port: ' )
    nId = getpass('Please enter NTCT Token: ')
    file_name = '.serverdata.txt'  # Specify the file name
    with open(file_name, 'w') as file:
        # Step 3: Write input to the file
        file.write(server_ip+','+server_port+','+nId)
    return server_ip, server_port, nId

def read_server_data():
    file_decrypt = open('.serverdata.txt',"r")
    for line in file_decrypt:
        #Let's split the line into an array called "fields" using the "," as a separator
        fields = line.split(",")
        #and let's extract the data:
        server_ip = fields[0]
        server_port = fields[1]
        nId = fields[2]
    file_decrypt.close()
    return server_ip, server_port, nId

def curl_command(server_ip, server_port, nId):
    os.system(f'curl -k -X POST --cookie "NSSESSIONID={nId}" -k https://{server_ip}:{server_port}/dbonequerydata/query -H "Content-Type:application/xml" -H "Accept:text/csv" -d @util.xml -o util.csv')

def cleanup_csv(start_time):
    df = pd.read_csv('util.csv')  # Replace 'your_data.csv' with your actual CSV file path

    # Step 2: Round specific columns
    columns_to_round = ['bitRate', 'packetRate', 'utilization']
#    columns_to_round = ['peakBitRate', 'peakPacketRate', 'utilization']
    decimal_places = 2
    df[columns_to_round] = df[columns_to_round].round(decimal_places)

    # Step 3: Concatenate the original DataFrame with the rounded columns
    rounded_columns = [f'{col}_rounded' for col in columns_to_round]
    df_concatenated = pd.concat([df, df[columns_to_round].add_suffix('_rounded')], axis=1)

    # Step 4: Save the concatenated DataFrame to a new CSV file
    output_file = f'rounded_data_with_original-{start_time}.csv'
    df_concatenated.to_csv(output_file, index=False)

def cleanup_final(start_time):
    df = pd.read_csv(f'rounded_data_with_original-{start_time}.csv')  # Replace 'your_data.csv' with your actual CSV file path
    df = df[['ipAddress', 'ifn', 'bitRate_rounded', 'packetRate_rounded', 'utilization_rounded']]
#    df = df[['ipAddress', 'ifn', 'peakBitRate_rounded', 'peakPacketRate_rounded', 'utilization_rounded']]

    # Replace with your desired column names

    new_column_names = {
        'bitRate_rounded': 'bitRate(Kbps)',
        'packetRate_rounded': 'packetRatge(pps)',
        'utilization_rounded': 'utilization',
        # Add more mappings as needed
    }
    '''
    new_column_names = {
        'peakBitRate_rounded': 'bitRate(Kbps)',
        'peakPacketRate_rounded': 'packetRatge(pps)',
        'utilization_rounded': 'utilization',
        # Add more mappings as needed
    }

    '''

    # Rename columns
    df.rename(columns=new_column_names, inplace=True)
    # Column from which to get the top ten values
    column_name = 'bitRate(Kbps)'

    # Get top ten values based on 'Values' column
    top_ten = df.nlargest(10, column_name)
    # Column from which to get the top ten values
    column_n = 'packetRatge(pps)'

    # Get top ten values based on 'Values' column
    top_ten_pps = df.nlargest(10, column_n)


    with pd.ExcelWriter(f'ISNG_capacity_{start_time}.xlsx', engine='xlsxwriter') as writer:
        # Write each DataFrame to a specific sheet
        df.to_excel(writer, sheet_name='All-data', index=False)
        top_ten.to_excel(writer, sheet_name='Top-Ten-BitRate', index=False)
        top_ten_pps.to_excel(writer, sheet_name='Top-Ten-PPS', index=False)
        # Get the xlsxwriter workbook and worksheet objects.
        workbook  = writer.book
        worksheet = writer.sheets['All-data']
        worksheet1 = writer.sheets['Top-Ten-BitRate']
        worksheet2 = writer.sheets['Top-Ten-PPS']
        # Add a number format with thousand separator to the 'Population' column.
        format_thousands = workbook.add_format({'num_format': '#,##0'})
        worksheet.set_column('C:C', None, format_thousands)
        worksheet.set_column('D:D', None, format_thousands)
        worksheet1.set_column('C:C', None, format_thousands)
        worksheet1.set_column('D:D', None, format_thousands)
        worksheet2.set_column('C:C', None, format_thousands)
        worksheet2.set_column('D:D', None, format_thousands)

#    df.to_csv('ISNG_with_traffic_{start_time}.csv', index=False)
    print('This final version of requested data is as follows alltraffic_filtered.csv')
    print('Script completed')
def cleanup_files():
    os.system('rm -fr *rounded*.csv')
    os.system('rm -fr util.csv')

print(f'PSS ISNG Capacity report -Script version 1.3 Author James Vigliotti')

if platform.system() =='Windows':
    p_version = sys.version
    p_os = platform.platform()
    print('Script is running on '+p_os+' running python version '+p_version)
else:
    p_version = sys.version
    p_os = distro.name()
    p_dver = distro.version()
    print('Script was tested on '+p_os+' '+p_dver+' running python version '+p_version)

file = pathlib.Path('.serverdata.txt')
if not file.exists ():
    server_ip,server_port,nId = nG1_login_data()
else:
    server_ip,server_port,nId = read_server_data()
#print(server_ip,server_port,nId, sep=',')
network_id = input('Please enter Network Service like to use - All Locations: ')
start_time = xml_file(network_id)
curl_command(server_ip, server_port, nId)
cleanup_csv(start_time)
cleanup_final(start_time)
cleanup_files()