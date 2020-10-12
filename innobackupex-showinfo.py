#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
name:          inno-showinfo.py
description:   Show information about incremental innobackupex backups
version:       0.1
tested on:     Debian Wheezy, RHEL5
"""

import os
import sys
import argparse
import datetime
import subprocess

# Global variables.
DESCRIPTION='''
Show information about innobackupex backups
        
  Assumption: 
  * either all full and incr are located in the same parent dir,
  * or all full are located in one parent dir
    and all incr are located in another parent dir (see "-a")'''
XTRABACKUP_INFO = 'xtrabackup_info'
TOOL_NAME = 'tool_name'
INNOBACKUPEX = 'innobackupex'
START_TIME = 'start_time'
INCREMENTAL = 'incremental'
IS_SET = 'Y'
IS_NOT_SET = 'N'
SUPPORTED_PARAM = (INCREMENTAL,)
USER_CNF='.my.cnf'
MYSQL_LOGIN_PARAM_SOCKET = {'-S':'socket'}
MYSQL_LOGIN_PARAM_TCP = {'-h':'bind-address', '-P':'port'}

def is_readable(*args):
   """Check read permissions for passed paths."""
   for f in args:
      if not os.access(f, os.R_OK):
         print('%s: is not readable.' % f)
         sys.exit(1)

def chk_xtra_param(param, value, file_path):
   """Check if only supported parameters are enabled in XTRABACKUP_INFO."""
   for supported_param in SUPPORTED_PARAM:
      if param == supported_param:
         return
   if param == TOOL_NAME and value != INNOBACKUPEX:
      print('%s --> "%s" "%s" is not supported.' % (file_path, param, value))
      sys.exit(1)
   if value == IS_SET:
      print('%s --> Enabled param "%s" is not supported.' % (file_path, param))
      sys.exit(1)

def get_value(param, defaults_file, exit_on_empty=True, param_only=False):
   """Return value for passed parameter or check existence of param. 
      Read from passed file."""
   try:
      fh = open(defaults_file)
      for line in fh:
         if line.startswith(param):
            if param_only:
               return True
            else:
               value = line.split('=')[1].strip()
               return value
      if not exit_on_empty:
         return False
   finally:
      fh.close()

   print('Could not determine param "%s" in defaults-file %s.' % (param, defaults_file))
   sys.exit(1)

def main():
   """Run the main script body."""
   parser = argparse.ArgumentParser(
      description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
   parser.add_argument("-d",
      dest="defaults_file",
      metavar="defaults-file",
      default="/etc/mysql/my.cnf",
      help='specify path to "defaults-file" (default: /etc/mysql/my.cnf)')
   parser.add_argument("-u",
      dest="user_cnf",
      metavar="user-cnf",
      default=".my.cnf",
      help='specify path to "user-cnf" (default: $HOME/.my.cnf)')
   group = parser.add_mutually_exclusive_group(required=True)
   group.add_argument("-o",
      dest="backup_dir",
      metavar="backup-dir",
      help='show overview of full and incr in "backup-dir in chronological order, \
         specify parent dir where all full and incr are located')
   group.add_argument("-l",
      dest="last_incr_dir",
      metavar="last-incr-dir",
      help="show needed commands to restore an incr backup, \
         specify dir of last incr backup to be applied")
   parser.add_argument("-a",
      dest="additional_dir",
      metavar="additional-dir",
      help='specify parent dir of full or incr if one type is not \
         located in "backup-dir" or specify parent dir of full if \
         not in parent dir of "last-incr"')
   parser.add_argument('-v', '--version',
      action='version',
      version='%(prog)s version 0.1')
   args = parser.parse_args()

   timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
   defaults_file = os.path.abspath(args.defaults_file)
   is_readable(defaults_file)

   if args.backup_dir:
      backup_dir = os.path.abspath(args.backup_dir)
      is_readable(backup_dir)
      search_dir = [backup_dir]
      reverse_bool = False

   if args.last_incr_dir:
      last_incr_dir = os.path.abspath(args.last_incr_dir)

      # Look for XTRABACKUP_INFO file.
      try:
         fh = open(os.path.join(last_incr_dir, XTRABACKUP_INFO))
      except IOError, error_msg:
         print('%s. Specify the correct path to incr!' % error_msg)
         sys.exit(1)
      fh.close()

      parent_backup_dir = os.path.dirname(last_incr_dir)
      is_readable(parent_backup_dir, last_incr_dir)
      search_dir = [parent_backup_dir]
      reverse_bool = True
      incr_backup_found = False
      full_backup_found = False

   if args.additional_dir:
      additional_dir = os.path.abspath(args.additional_dir)
      is_readable(additional_dir)
      search_dir.append(additional_dir)

   # Scan search_dir for XTRABACKUP_INFO files and store data in dictionary.
   dir_dict = {}
   for path in search_dir:
      for root, dirs, files in os.walk(path):
         for f in files:
            if f == XTRABACKUP_INFO:
               file_path = os.path.join(root, f)
               try:
                  fh = open(file_path)
                  for line in fh:
                     param = line.split('=')[0].strip()
                     value = line.split('=')[1].strip()
                     chk_xtra_param(param, value, file_path)

                     if line.startswith(START_TIME):
                        start_time = value
                     if line.startswith(INCREMENTAL):
                        is_incremental = value

                  dir_dict[start_time] = [os.path.dirname(file_path), is_incremental]
               
               finally:
                  fh.close()

   if len(dir_dict) == 0:
      print('Could not find any "%s" file in %s.' % (XTRABACKUP_INFO, search_dir))
      sys.exit(1)

   if args.backup_dir: 
      print('Overview of full and incremental:\n')

   # Loop over sorted dirctionary.
   for key in sorted(dir_dict, reverse=reverse_bool):
      dir_name = dir_dict[key][0]
      is_readable(dir_name)
      is_incremental = dir_dict[key][1]

      # Print overview of full and incr.
      if args.backup_dir:
         if is_incremental == IS_NOT_SET:
            print('Full --> %s' % dir_name)
         if is_incremental == IS_SET:
            print('Incr --> %s' % dir_name)

      # Check for last_incr_dir and find related full.
      if args.last_incr_dir:
         if dir_name == last_incr_dir:
            incr_backup_dir = dir_name
            incr_backup_found = True
         if incr_backup_found and is_incremental == IS_NOT_SET:
            full_backup_dir = dir_name
            full_backup_found = True
            break

   if args.last_incr_dir and not full_backup_found:
      print('%s --> ERROR: Could not find related full backup. Consider using "-a".' % last_incr_dir)
      sys.exit(1)

   if args.last_incr_dir:
      mysql_login_param = ""
      datadir = get_value('datadir', defaults_file)
      mysqld_user = get_value('user', defaults_file)

      # Determine path of user cnf file.
      if args.user_cnf:
         user_cnf_path = os.path.abspath(args.user_cnf)
      else:
         homedir = os.path.expanduser('~')
         user_cnf_path = os.path.join(homedir, USER_CNF)

      user_cnf_valid = False
      if os.access(user_cnf_path, os.R_OK):
         mysql_login_param = "".join(['--defaults-file=', user_cnf_path])
         mysql_query = "select Shutdown_priv from mysql.user where user = SUBSTRING_INDEX(CURRENT_USER(),'@',1) and host = SUBSTRING_INDEX(CURRENT_USER(),'@',-1);"
         cmd = ['mysql', mysql_login_param, '-NBe', mysql_query]
         # Check if shutdown_priv is available for user in user_cnf.
         # This is not 100% straight forward because the Select_priv for mysql db must be given.
         chk_shutdown_priv = subprocess.Popen(cmd, stdout=subprocess.PIPE)
         chk_shutdown_priv_stdout = chk_shutdown_priv.communicate()
         # chk_shutdown_priv_stdout is a tuple.
         if chk_shutdown_priv_stdout[0].rstrip('\n') == 'Y':
            user_cnf_valid = True
         else:
            print('ERROR on executing: "%s"' % (cmd))
            sys.exit(1)

      if not user_cnf_valid:
         # Determine mysql login parameter.
         skip_networking = get_value('skip-networking', defaults_file, exit_on_empty=False, param_only=True)
         if skip_networking:
            MYSQL_LOGIN_PARAM = MYSQL_LOGIN_PARAM_SOCKET
         else:
            MYSQL_LOGIN_PARAM = MYSQL_LOGIN_PARAM_TCP

         for param in MYSQL_LOGIN_PARAM:
            value = get_value(MYSQL_LOGIN_PARAM[param], defaults_file, exit_on_empty=False)
            if value:
               mysql_login_param = " ".join([mysql_login_param, param, value]).strip()

         mysql_login_param = " ".join([mysql_login_param, '-p'])

      print('Restore commands:\n')
      print('mysqladmin %s shutdown' % mysql_login_param)
      print('mv %s %s_%s' % (datadir, datadir, timestamp))
      print('mkdir %s' % datadir)
      # Check when to apply logs without "--redo-only" option.
      full_backup_found = False
      for key in sorted(dir_dict):
         path = dir_dict[key][0]
         is_incremental = dir_dict[key][1]

         if path == full_backup_dir:
            restore_full_backup_dir = full_backup_dir + "_MERGED"
            print('# Applying logs is irreversible and would destroy the backup history, therefore making a copy.')
            print('cp -a %s %s' % (full_backup_dir, restore_full_backup_dir))
            print('innobackupex --defaults-file=%s --apply-log --redo-only %s' % (defaults_file, restore_full_backup_dir))
            full_backup_found = True

         if full_backup_found and is_incremental == IS_SET:
            prev_dir = path
            if path != incr_backup_dir:
               print('innobackupex --defaults-file=%s --apply-log --redo-only %s --incremental-dir=%s' % (defaults_file, restore_full_backup_dir, prev_dir))
            else:
               print('innobackupex --defaults-file=%s --apply-log %s --incremental-dir=%s' % (defaults_file, restore_full_backup_dir, prev_dir))
               print('innobackupex --defaults-file=%s --copy-back %s' % (defaults_file, restore_full_backup_dir))
               print('chown -R %s:%s %s' % (mysqld_user, mysqld_user, datadir))
               break
   
if __name__ == '__main__':
   main()

