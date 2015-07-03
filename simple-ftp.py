__author__ = 'yuguang'

from ftplib import FTP
ftp = FTP()
ftp.connect('mini.resl.uwaterloo.ca', 21)
ftp.login()
ftp.cwd('worker-eb986072-4ad4-44e2-a90a-978a24745360')
ftp_list = ftp.nlst()