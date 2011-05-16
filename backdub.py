#!/usr/bin/python

import os
import sys
import datetime
import ConfigParser

VERSION = "0.02a"

CONFIG_FILE = "./config"
LOGLEVELS = {"DEBUG" : 0, "INFO" : 1, "NOTICE" : 2, "WARN" : 3, "ERROR" : 4}

# These can be set in the config file
BACKUP_PATH = None
LOGLEVEL = "DEBUG"

class Target:
  def __init__(self, path):
    # Remember the path of the target file
    self.path = path
    # Set the filename as the name of the target
    self.name = os.path.split(path)[1]
    # Parse paths from the file
    self.paths = self.read_paths(self.path)
    plog("INFO", "Initialized target '" + self.name + "'")

  def read_paths(self, filename):
    """ Read a list of paths from a file """
    try:
      file = open(filename, 'r')
      lines = file.readlines()
      file.close()
    except IOError:
      plog("ERROR", "Targetfile '" + filename + "' is not existing/readable!")
      sys.exit(1)
    # Clear paths
    paths = []
    for l in lines:
      # Split to single values
      splitted = l.split()
      if len(splitted) > 0:
        p = splitted[0]
        paths.append(p)
        plog("DEBUG", "Added path: "+p)
    return paths

  def backup(self):
    """ Create a zipped tape archive """
    if len(self.paths) >= 1:
      # We have at least one path, generate the archive filename
      today = str(datetime.date.today())
      tarfile = BACKUP_PATH + "/" + self.name + "." + today + ".tar"
      for p in self.paths:
        if os.path.exists(p):
          plog("INFO", "Path exists: " + p)
          plog("DEBUG", "split 0: " + os.path.split(p)[0] + ", split 1: "
             + os.path.split(p)[1])
          # Change to parent directory in any case
          # FIXME: This will not work for target paths on the root level
          command = "cd " + os.path.split(p)[0] + ";"
          # Create archive or append
          if not os.path.exists(tarfile):
            command += "tar -cvf " + tarfile + " " + os.path.split(p)[1]
            plog("DEBUG", "Command: << " + command + " >>")
            plog("INFO", "Creating archive of " + p + " to " + tarfile)
          else:
            command += "tar -rvf " + tarfile + " " + os.path.split(p)[1]
            plog("DEBUG", "Command: << " + command + " >>")
            plog("INFO", "Appending " + p + " to " + tarfile)
          os.system(command)
        else:
          self.paths.remove(p)
          plog("WARN","Path doesn't exist! Remove '" + p + "' from target '"
             + self.name + "'?")
      # Zip the archive
      os.system("gzip " + tarfile)
      plog("INFO", "Backup finished on target '" + self.name + "'")
      # DEBUG: Print out the return value of the last command
      os.system("echo '[Return value: '$?']'")

def plog(level, msg):
  """ Log messages to stdout """
  # TODO: Add timestamps
  if(LOGLEVELS[level] >= LOGLEVELS[LOGLEVEL]):
    print level + ": " + msg
    sys.stdout.flush()

def configure(config_file):
  """ Read configuration from a given file """
  config = ConfigParser.SafeConfigParser()
  if os.path.exists(config_file):
    plog("DEBUG", "Loading configuration from file '" + config_file + "'")
    config.read(config_file)
  else:
    plog("ERROR", "Configuration file '" + config_file
       + "' does not exist, exiting.")
    sys.exit(0)
  # Set the backup path
  global BACKUP_PATH
  BACKUP_PATH = config.get("GENERAL", "BACKUP_PATH")
  plog("DEBUG", "BACKUP_PATH is "+BACKUP_PATH)
  # Set the log level
  global LOGLEVEL
  LOGLEVEL = config.get("GENERAL", "LOGLEVEL")

if __name__ == '__main__':
  """ Program entry point """
  plog("INFO", "backdub v" + str(VERSION))
  if len(sys.argv) != 2:
    plog("NOTICE", "Usage is \"./backdub.py <targetfile>\"")
  else:
    configure(CONFIG_FILE)
    # Instanciate the given target and back it up
    target = Target(sys.argv[1])
    target.backup()

