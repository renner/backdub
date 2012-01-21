#!/usr/bin/python
# Copyright (c) Johannes Renner 2011, see LICENSE file.

import os
import sys
import datetime
import ConfigParser

VERSION = "0.0.3a"

CONFIG_FILE = "./config"
LOGLEVELS = {"TRACE" : 0, "DEBUG" : 1, "INFO" : 2, "NOTICE" : 3, "WARN" : 4, "ERROR" : 5}
VERBOSE = False

# Override these in the config file
BACKUP_PATH = os.getcwd()
LOGLEVEL = "INFO"

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
        plog("DEBUG", "Added path: " + p)
    return paths

  def backup(self, timestamp=None):
    """ Create a zipped tape archive of the contents """
    if len(self.paths) >= 1:
      # We have at least one path, generate the archive filename
      if not timestamp:
        timestamp = get_timestamp()
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
      plog("NOTICE", "Backup finished on target '" + self.name + "'")
      # Print the return value of the last command
      if (LOGLEVELS["DEBUG"] >= LOGLEVELS[LOGLEVEL]):
        os.system("echo '[Return value: '$?']'")

def we_need_to_log(level):
  """ Check if we need to log """
  return LOGLEVELS[level] >= LOGLEVELS[LOGLEVEL]

def get_timestamp(pattern="%Y-%m-%d-%H%M%S"):
  """ Get a timestamp using the given pattern """
  return datetime.datetime.now().strftime(pattern)

def plog(level, msg, ex=None):
  """ Log a message to stdout """
  if we_need_to_log(level):
    timestamp = get_timestamp("%Y-%m-%d-%H:%M:%S")
    msg = timestamp + " [" + level + "]: " + msg
    if ex:
      msg += " (" + str(ex) + ")"
    print msg
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
    plog("NOTICE", "Setting default LOGLEVEL: " + LOGLEVEL, e)
  # Print a welcome message
  plog("INFO", "backdub-" + str(VERSION))
  try:
    global BACKUP_PATH
    BACKUP_PATH = config.get("GENERAL", "BACKUP_PATH")
  except Exception as e:
    plog("NOTICE", "Writing backups to CWD: " + BACKUP_PATH, e)
  finally:
    plog("DEBUG", "BACKUP_PATH is " + BACKUP_PATH)
  # Set verbosity for tar
  if we_need_to_log("TRACE"):
    VERBOSE = True

def backup(target, prefix="", timestamp=None):
    """ Recursively call backup on target files or dirs """
    if not prefix == "":
      target = prefix + "/" + target
    if os.path.isdir(target):
      plog("DEBUG", "Directory: " + target)
      listing = os.listdir(target)
      for item in listing:
        backup(item, target, timestamp)
    else:
      plog("DEBUG", "Targetfile: " + target)
      target = Target(target)
      target.backup(timestamp)

if __name__ == '__main__':
  """ Program entry point """
  if len(sys.argv) < 2:
    plog("ERROR", "Usage is \"./backdub.py <targetfile>\"")
  else:
    configure(CONFIG_FILE)

    # Handle commandline options
    if len(sys.argv) > 2:
      # Init options
      options = sys.argv[2]
      if options:
        plog("ERROR", "Unsupported options: " + sys.argv[2])
        sys.exit()

    # Get started on given target
    backup(sys.argv[1], timestamp=get_timestamp())

