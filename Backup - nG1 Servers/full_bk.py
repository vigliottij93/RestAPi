import psutil
import time
import os
from timeit import default_timer as timer
import datetime
import subprocess
import os.path
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

# Setup logging with rotation
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = "/opt/backup/rsync_log.txt"

handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
handler.setFormatter(log_formatter)
handler.suffix = "%Y-%m-%d"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    # Iterate over all the running processes
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def convert(n):
    return str(datetime.timedelta(seconds = n))

def rsync_net_dir():
    # Calls the rsync command
    rsync_m = os.popen("rsync -avhW  --exclude 'dbone' --exclude 'pmupgrade' --exclude 'tftpboot' --stats /opt/NetScout/ /nfs-mount/NetScout/")
    rsync_move = rsync_m.read()
    logger.info(rsync_move)

def rysnc_db_dir():
    rsync_db = os.popen('rsync --sparse=always -avhW --stats /opt/NetScout/rtm/database/ /nfs-mount/NetScout/rtm/database/')
    rsync_db_r = rsync_db.read()
    logger.info(rsync_db_r)

def calc_Netscout():
    # Gets the size of the NetScout directory including the DBone directories.
    dbone_fs = os.popen("du -sh /opt/NetScout/")
    dbone_r = dbone_fs.read()
    logger.info(dbone_r)

def mount_nfs_bk():
    mount_nfs = os.popen('mount 172.23.246.54:/opt/nG1-NFS/nsc01094p01 /nfs-mount').read()
    # logger.info(mount_nfs)  # Uncomment if you want to log the mount output

def mount_check():
    # Path
    path = "/nfs-mount"
    # Check whether the given path is a mount point or not
    ismount = os.path.ismount(path)
    return ismount

# Creates the timer for measuring the script execution time
st = timer()
# Check NFS mount if mounted on system or not, automatically mount if missing
nfs_check = mount_check()
if not nfs_check:
    logger.info('Mounting NFS')
    mount_nfs_bk()
    logger.info('Checking if mount was successful')
    nfs_chk_mount = mount_check()
    if not nfs_chk_mount:
        logger.error('Mount failed')
        sys.exit()
    else:
        logger.info('Mount successful')
else:
    logger.info('Mount exists')

# Gets the date and writes to the log file
date_s = os.popen('date').read()
logger.info(date_s)
calc_Netscout()

# Check if any rsync process was running or not.
if checkIfProcessRunning('rsync'):
    logger.info('rsync is still running, exiting')
    sys.exit()
else:
    logger.info('No rsync process was running')
    rsync_net_dir()
    # Check to see if the rsync for the Netscout directory has been completed
    if checkIfProcessRunning('rsync'):
        logger.info('rsync is still running, exiting')
        sys.exit()
    else:
        logger.info('No rsync process was running')
        rysnc_db_dir()

end_time = timer() - st
elapsed_time = convert(end_time)
logger.info('Execution time: ' + elapsed_time)
