#!/usr/bin/env python3

import platform
import distro
import os
import subprocess
import sys
from scp import SCPClient
import configparser
from pathlib import Path
import paramiko
import csv
import logging
from colorama import Fore, Style, init

#DEFAULT_PASSWORD = 'netscout1'
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

log_filename='menu_user_log.txt'
logger = create_logging_function(log_filename)

def get_config():
    # Define the path for the config file
    config_file_path = '.config.ini'
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    # Read the configuration file
    config.read(config_file_path)
    # Access variables for script
    username = config.get('settings', 'username')
    userpass = config.get('settings', 'password')
    ssh_port = config.get('settings', 'ssh_port')
    del_devices = config.get('settings', 'del_devices')
    del_accounts = config.get('settings', 'del_accounts')
    add_devices = config.get('settings', 'add_devices')
    add_accounts = config.get('settings', 'add_accounts') 
    DEFAULT_PASSWORD = config.get('settings', 'new_user_default_pass')
    return  username, userpass, ssh_port,  del_devices , del_accounts, add_devices, add_accounts, DEFAULT_PASSWORD

def show_menu():
    print("===== Menu =====")
    print("1. add new User Accounts")
    print("2. delete User Accounts")
    print("3. Exit")
    print("================")

def user_exists(ssh_client, username):
    stdin, stdout, stderr = ssh_client.exec_command(f'id -u {username}')
    return stdout.channel.recv_exit_status() == 0

def create_user(ssh_client, username, destination_host,  DEFAULT_PASSWORD):
    logger.info(f"Creating user {username} on {destination_host}")
    commands = [
        f'useradd -m {username}',
        f'echo "{username}:{DEFAULT_PASSWORD}" | chpasswd',
        f'chage -d 0 {username}'
    ]
    for command in commands:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        stdout.channel.recv_exit_status()  # Wait for command to complete
    logger.info(f"User {username} created successfully on {destination_host}")

def grant_sudo_privileges(ssh_client, username, destination_host):
    # Check if the user is already in the sudoers file
    check_command = f"sudo grep -q '^{username} ALL=(ALL:ALL) ALL' /etc/sudoers"
    stdin, stdout, stderr = ssh_client.exec_command(check_command)

    if stdout.channel.recv_exit_status() != 0:  # User not found in sudoers
        logger.info(f"Granting sudo privileges to user {username} on {destination_host}")

        # Allow running sudo without a TTY
#        grant_command = f"echo '{username} ALL=(ALL) NOPASSWD: ALL' | sudo tee -a /etc/sudoers"
        grant_command = f"sed -i '/^root[[:space:]]*ALL=[[:space:]]*(ALL)[[:space:]]*ALL/a {username} ALL=(ALL) NOPASSWD: ALL' /etc/sudoers"
        ssh_client.exec_command(grant_command)

        logger.info(f"Sudo privileges granted for user {username} on {destination_host}")
    else:
        logger.info(f"Sudo privileges already granted for user {username} on {destination_host}")

def check_users(ssh_client, username, destination_host):
    # Command to check users starting with 'n_'
    command = f"grep '{username}' /etc/passwd"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    # Read output and errors
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if output:
        logger.info(f"Checking for {username} on {destination_host}:\n{output}")
    else:
        logger.info(f"{username} was not  found on {destination_host}.")

    if error:
        logger.critical(f"Error: {error}")

def isng_delete(username,userpass,host_arg1,ssh_port,del_user):
    logger.info(f'Deleting useraccount {del_user} for {host_arg1}')
    # Create an SSH client object
    client = paramiko.SSHClient()

    # Automatically add the server's host key (for simplicity; in production, handle keys properly)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the remote server
        client.connect(host_arg1, port=ssh_port, username=username, password=userpass)
        # Execute a command
        command = f'userdel -r {del_user}'  # Replace with the command you want to run
        stdin, stdout, stderr = client.exec_command(command)
#        with open('del_user_log.txt', 'a') as bk_file:
        # Print command output
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if output:
            logger.info(f"Output for deleting {del_user} from  {host_arg1}:")
            logger.info(stdout.read().decode())
        # Print any errors
        if error:
            logger.critical(f"Errors for deleting {del_user} from {host_arg1}:")
            logger.critical(stderr.read().decode())
        command1 = 'grep "n_" /etc/passwd'  # Replace with the command you want to run
        stdin, stdout, stderr = client.exec_command(command1)
#        with open('del_user_log.txt', 'a') as bk_file:
        # Print command output
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if output:
            logger.info(f"Output verification of user delete {host_arg1}:")
            logger.info(stdout.read().decode())
        # Print any errors
        if error:
            logger.critical(f"Error: {error}")
            logger.critical(f"Errors for user delete {host_arg1}:")
            logger.critical(stderr.read().decode())
        command2 = f"sed -i '/{del_user}/d' /etc/sudoers"
        stdin, stdout, stderr = client.exec_command(command2)
#        with open('del_user_log.txt', 'a') as bk_file:
        # Print command output
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if output:
            logger.info(f"Output for removing sudeor from  {host_arg1}:")
            logger.info(stdout.read().decode())
        # Print any errors
        if error:
            logger.critical(f"Error: {error}")
            logger.critical(f"Errors for removing sudeor from {host_arg1}:")
            logger.critical(stderr.read().decode())
        
    finally:
        # Close the connection
        client.close()
#    logger.info(f'Completed deleting of users  on {host_arg1}')
 
def file_count(file):
    file_path = file
    # Initialize line counter
    line_count = 0
    path = Path(file_path)
    if not path.is_file():
       logger.info('No device list file')
    else: 
        # Open the file and count lines
        with open(file_path, 'r') as file:
            for line in file:
                line_count += 1
        return line_count  

def main():
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
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            username, userpass, ssh_port, del_devices, del_accounts, add_devices, add_accounts, DEFAULT_PASSWORD = get_config()
            with open(add_devices, 'r') as host_file:
                for destination_host in host_file:
                    destination_host = destination_host.strip()  # Remove any whitespace/newline
                    # Create an SSH client
                    ssh1 = paramiko.SSHClient()
                    ssh1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    try:
                        ssh1.connect(destination_host, username=username, password=userpass, timeout=10)
                        # With statement with user names
                        with open(add_accounts, 'r') as user_file:
                            for destination_user in user_file:
                                destination_user = destination_user.strip()
                                if not user_exists(ssh1, destination_user):
                                    create_user(ssh1, destination_user, destination_host,  DEFAULT_PASSWORD)
                                    grant_sudo_privileges(ssh1, destination_user, destination_host)
                                else:
                                    logger.info(f"User {destination_user} already exists on {destination_host}")
                                check_users(ssh1, destination_user, destination_host)
                    except paramiko.SSHException as e:
                        logger.critical(f"SSH error on {destination_host}: {e}")
                    except Exception as e:
                        logger.critical(f"Error processing {destination_host}: {e}")
                    finally:
                        ssh1.close()
                    logger.info("Completed new users additions")
        if choice == '2':
            username, userpass, ssh_port, del_devices, del_accounts, add_devices, add_accounts, DEFAULT_PASSWORD = get_config()
            with open(del_devices, 'r') as hosts:
                for line in hosts:
                    host_arg1=line.strip()
                    try:
                        with open(del_accounts, 'r') as file:
                            for line in file:
                            # Strip leading/trailing whitespace and skip empty lines
                                hostname = line.strip()
                                isng_delete(username,userpass,host_arg1,ssh_port,hostname)
                 
                    except FileNotFoundError:
                        logger.info(f"File not found: {file_path}")
                    except Exception as e:
                        logger.critical(f'Exception {e}')
#                    logger.info(f'Completed deleting of users  on {host_arg1}')

        elif choice == '3':
            logger.info("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from menu.")

if __name__ == "__main__":
    main()

