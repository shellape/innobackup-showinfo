# innobackupex-showinfo.py

## Description
innobackupex-showinfo.py provides information about existing innobackupex backups (full and incremental).
To gather information (like tool_name, start_time, datadir, port, etc.) it parses xtrabackup_info and my.cnf file.

## Features
- Show overview about the relation between full and incremental backups.
- Show needed commands to restore up to a certain incremental backup.

## Built in help
```
$> innobackupex-showinfo.py -h
usage: innobackupex-showinfo.py [-h] [-d defaults-file] [-u user-cnf]
                                (-o backup-dir | -l last-incr-dir)
                                [-a additional-dir] [-v]

Show information about innobackupex backups
        
  Assumption: 
  * either all full and incr are located in the same parent dir,
  * or all full are located in one parent dir
    and all incr are located in another parent dir (see "-a")

optional arguments:
  -h, --help         show this help message and exit
  -d defaults-file   specify path to "defaults-file" (default:
                     /etc/mysql/my.cnf)
  -u user-cnf        specify path to "user-cnf" (default: $HOME/.my.cnf)
  -o backup-dir      show overview of full and incr in "backup-dir in
                     chronological order, specify parent dir where all full
                     and incr are located
  -l last-incr-dir   show needed commands to restore an incr backup, specify
                     dir of last incr backup to be applied
  -a additional-dir  specify parent dir of full or incr if one type is not
                     located in "backup-dir" or specify parent dir of full if
                     not in parent dir of "last-incr"
  -v, --version      show program's version number and exit
```

## Examples
```
# Get an overview about full and incremental backups:
$> innobackupex-showinfo.py -o /backup
Overview of full and incremental:

Full --> /backup/mysql1/2014-11-29_10-30-00
Incr --> /backup/mysql1/2014-11-29_11-30-00
Incr --> /backup/mysql1/2014-11-29_12-30-00
Full --> /backup/mysql2/2014-11-29_10-00-00
Incr --> /backup/mysql2/2014-11-29_12-00-00
Incr --> /backup/mysql2/2014-11-29_14-00-00
Incr --> /backup/mysql2/2014-11-29_16-00-00


# Show restore commands if full and incremental backups are located in the same directory:
$> innobackupex-showinfo.py -l /bkp/2014-11-29_14-00-00/
Restore commands:

mysqladmin -h 127.0.0.1 -P 3306 -p shutdown
mv /var/lib/mysql /var/lib/mysql_2014-11-29_16-08
mkdir /var/lib/mysql
# Applying logs is irreversible and would destroy the backup history, therefore making a copy.
cp -a /bkp/2014-11-29_09-00-00 /bkp/2014-11-29_09-00-00_MERGED
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_10-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_11-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_12-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_13-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_14-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --copy-back /bkp/2014-11-29_09-00-00_MERGED
chown -R mysql:mysql /var/lib/mysql


# Show restore commands with custom defaults-file and user-cnf file:
$> innobackupex-showinfo.py -d /etc/mysql/instance02.cnf -u /root/.instance02.cnf -l /bkp/2014-11-29_14-00-00/
Restore commands:

mysqladmin --defaults-file=/root/.instance02.cnf shutdown
mv /var/lib/mysql3307 /var/lib/mysql3307_2015-10-03_09-35
mkdir /var/lib/mysql3307
# Applying logs is irreversible and would destroy the backup history, therefore making a copy.
cp -a /bkp/2014-11-29_09-00-00 /bkp/2014-11-29_09-00-00_MERGED
innobackupex --defaults-file=/etc/mysql/instance02.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_10-00-00
innobackupex --defaults-file=/etc/mysql/instance02.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_11-00-00
innobackupex --defaults-file=/etc/mysql/instance02.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_12-00-00
innobackupex --defaults-file=/etc/mysql/instance02.cnf --apply-log --redo-only /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_13-00-00
innobackupex --defaults-file=/etc/mysql/instance02.cnf --apply-log /bkp/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/2014-11-29_14-00-00
innobackupex --defaults-file=/etc/mysql/instance02.cnf --copy-back /bkp/2014-11-29_09-00-00_MERGED
chown -R mysql:mysql /var/lib/mysql3307


# Show restore commands if full and incremental backups are located in different directories:
$> innobackupex-showinfo.py -l /bkp/incr/2014-11-29_14-00-00/ -a /bkp/full
Restore commands:

mysqladmin -h 127.0.0.1 -P 3306 -p shutdown
mv /var/lib/mysql /var/lib/mysql_2014-11-29_16-08
mkdir /var/lib/mysql
# Applying logs is irreversible and would destroy the backup history, therefore making a copy.
cp -a /bkp/full/2014-11-29_09-00-00 /bkp/full/2014-11-29_09-00-00_MERGED
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/full/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/incr/2014-11-29_10-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/full/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/incr/2014-11-29_11-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/full/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/incr/2014-11-29_12-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log --redo-only /bkp/full/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/incr/2014-11-29_13-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --apply-log /bkp/full/2014-11-29_09-00-00_MERGED --incremental-dir=/bkp/incr/2014-11-29_14-00-00
innobackupex --defaults-file=/etc/mysql/my.cnf --copy-back /bkp/full/2014-11-29_09-00-00_MERGED
chown -R mysql:mysql /var/lib/mysql
```
