import platform
import distro
import os
import subprocess
import sys
from scp import SCPClient
import configparser
from pathlib import Path
import paramiko

#Script version 2.1
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
    host_file = config.get('settings', 'hostlist')
    return  username, userpass, ssh_port, host_file

def show_menu():
    print("===== Menu =====")
    print("1. Run impi backup on devices")
    print("2. Change ipmi Password for devices")
    print("3. Exit")
    print("================")


def isng_call(username,userpass,host_arg1,ssh_port):

    print(f'Starting impi backup for {host_arg1}')
    # Create an SSH client object
    client = paramiko.SSHClient()

    # Automatically add the server's host key (for simplicity; in production, handle keys properly)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the remote server
        client.connect(host_arg1, port=ssh_port, username=username, password=userpass, timeout=10)
        # Execute a command
        command = '/opt/platform/RMM/rmmconfig.sh -p'  # Replace with the command you want to run
        stdin, stdout, stderr = client.exec_command(command)
        with open('ipmi_backup_log.txt', 'a') as bk_file:
            # Print command output
            print(f"Output for {host_arg1}:", file=bk_file)
            print(stdout.read().decode(), file=bk_file)
            # Print any errors
            print(f"Errors for {host_arg1}:", file=bk_file)
            print(stderr.read().decode(), file=bk_file)
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {host_arg1}.")

    except (paramiko.SSHException, paramiko.socket.socket.timeout, paramiko.socket.error) as e:
        print(f"Failed to connect to {host_arg1}: {e}")
    finally:
        # Close the connection
        client.close()
    print(f'Completed impi backup for {host_arg1}')

def isng_call_pass_chge(username,userpass,host_arg1,ssh_port):

    print(f'Starting impi password change for {host_arg1}')
    # Create an SSH client object
    client = paramiko.SSHClient()

    # Automatically add the server's host key (for simplicity; in production, handle keys properly)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Connect to the remote server
        client.connect(host_arg1, port=ssh_port, username=username, password=userpass, timeout=10)
        # Execute a command
        command = 'ipmitool user set password 2 4dih7LdY8e'  # Replace with the command you want to run
#        command = 'ipmitool'
        stdin, stdout, stderr = client.exec_command(command)
        with open('ipmi_pass_change_log.txt', 'a') as bk_file:
            # Print command output
            print(f"Output for {host_arg1}:", file=bk_file)
            print(stdout.read().decode(), file=bk_file)
            # Print any errors
            print(f"Errors for {host_arg1}:", file=bk_file)
            print(stderr.read().decode(), file=bk_file)
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {host_arg1}.")

    except (paramiko.SSHException, paramiko.socket.socket.timeout, paramiko.socket.error) as e:
        print(f"Failed to connect to {host_arg1}: {e}")
    finally:
        # Close the connection
        client.close()
    print(f'Completed impi password change for {host_arg1}')



def file_count(file):
    file_path = file
    # Initialize line counter
    line_count = 0
    path = Path(file_path)
    if not path.is_file():
        print('No device list file')
    else:
        # Open the file and count lines
        with open(file_path, 'r') as file:
            for line in file:
                line_count += 1
        return line_count

def main():
    print('Script Version 2.1')
    if platform.system() =='Windows':
        p_version = sys.version
        p_os = platform.platform()
        print('Script is running on '+p_os+' running python version '+p_version)
    else:
        p_version = sys.version
        p_os = distro.name()
        p_dver = distro.version()
        print('Script is running on '+p_os+' '+p_dver+' running python version '+p_version)

    while True:
        show_menu()
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            username, userpass, ssh_port, host_file = get_config()
            mib_cnt = file_count(host_file)
            print(f'Number of devices  to backup {mib_cnt}')
            #print(f'{username} , {userpass}, {ssh_port}, {host_file}')
            try:
                with open(host_file, 'r') as file:
                    for line in file:
                        # Strip leading/trailing whitespace and skip empty lines
                        hostname = line.strip()
                        isng_call(username,userpass,hostname,ssh_port)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except Exception as e:
                print(f'Exception {e}')

        elif choice == '2':
            username, userpass, ssh_port, host_file = get_config()
            mib_cnt = file_count(host_file)
            print(f'Number of devices  to change ipmi password {mib_cnt}')
            #print(f'{username} , {userpass}, {ssh_port}, {host_file}')
            try:
                with open(host_file, 'r') as file:
                    for line in file:
                        # Strip leading/trailing whitespace and skip empty lines
                        hostname = line.strip()
                        isng_call_pass_chge(username,userpass,hostname,ssh_port)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except Exception as e:
                print(f'Exception {e}')

        elif choice == '3':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from menu.")

if __name__ == "__main__":
    main()