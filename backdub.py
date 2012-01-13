#!/usr/bin/python
# Copyright (c) Johannes Renner 2011, see LICENSE file.

import os
import sys
import datetime
import ConfigParser

VERSION = "0.02a"

CONFIG_FILE = "./config"
LOGLEVELS = {"DEBUG" : 0, "INFO" : 1, "NOTICE" : 2, "WARN" : 3, "ERROR" : 4}
VERBOSE = False

# Override these in the config file
BACKUP_PATH = os.getcwd()
LOGLEVEL = "NOTICE"

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
    """ Create a zipped tape archive of the contents """
    if len(self.paths) >= 1:
      # We have at least one path, generate the archive filename
      timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
      tarfile = BACKUP_PATH + "/" + self.name + "." + timestamp + ".tar"
      zipfile = tarfile + ".gz"
      # Check if these files exist
      if os.path.exists(tarfile):
        os.remove(tarfile)
      if os.path.exists(zipfile):
        os.rename(zipfile, zipfile + ".OLD")
      # Iterate over target contents
      for p in self.paths:
        if os.path.exists(p):
          plog("DEBUG", "Path exists: " + p)
          plog("DEBUG", "split 0: " + os.path.split(p)[0] + ", split 1: "
             + os.path.split(p)[1])
          # Change to parent directory in any case
          # FIXME: This will not work for target paths on the root level
          command = "cd " + os.path.split(p)[0] + ";"
          # Handle 'verbose'
          options = "-"
          if VERBOSE:
            options += "v"
          # Create the archive or append to it
          if not os.path.exists(tarfile):
            options += "cf"
            command += "tar " + options + " " + tarfile + " " + os.path.split(p)[1]
            plog("DEBUG", "Command: << " + command + " >>")
            plog("INFO", "Creating archive of " + p + " to " + tarfile)
          else:
            options += "rf"
            command += "tar " + options + " " + tarfile + " " + os.path.split(p)[1]
            plog("DEBUG", "Command: << " + command + " >>")
            plog("INFO", "Appending " + p + " to " + tarfile)
          os.system(command)
        else:
          self.paths.remove(p)
          plog("WARN","Path doesn't exist! Remove '" + p + "' from target '"
             + self.name + "'?")
      # Zip the archive
      os.system("gzip " + tarfile)
      plog("INFO", "Backup finished on target '" + self.name + ".'")
      # DEBUG: Print out the return value of the last command
      os.system("echo '[Return value: '$?']'")

def plog(level, msg):
  """ Log messages to stdout """
  # TODO: Add timestamps
  if(LOGLEVELS[level] >= LOGLEVELS[LOGLEVEL]):
    print level + ": " + msg
    sys.stdout.flush()

def configure(config_file):
  """ Read configuration from a file """
  config = ConfigParser.SafeConfigParser()
  if os.path.exists(config_file):
    config.read(config_file)
  else:
    plog("NOTICE", "Config file '" + config_file
       + "' does not exist, running on default values.")
    return
  try:
    global LOGLEVEL
    LOGLEVEL = config.get("GENERAL", "LOGLEVEL")
  except Exception as e:
    plog("NOTICE", str(e) + " -> using default value: " + LOGLEVEL)
  try:
    global BACKUP_PATH
    BACKUP_PATH = config.get("GENERAL", "BACKUP_PATH")
  except Exception as e:
    plog("NOTICE", str(e) + " -> using cwd: " + BACKUP_PATH)
  finally:
    plog("DEBUG", "BACKUP_PATH is " + BACKUP_PATH)

if __name__ == '__main__':
  """ Program entry point """
  if len(sys.argv) < 2:
    plog("ERROR", "Usage is \"./backdub.py <targetfile> <options>\"")
  else:
    configure(CONFIG_FILE)
    plog("INFO", "backdub v" + str(VERSION))
    # Create target and back it up
    target = Target(sys.argv[1])

    # Handle options
    if len(sys.argv) > 2:
      # Init options
      options = sys.argv[2]
      if options and options == "-v":
        VERBOSE = True
      elif options:
        plog("ERROR", "Unsupported option: " + options)
        sys.exit()

    # Start the backup
    target.backup()

