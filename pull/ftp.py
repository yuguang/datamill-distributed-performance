from ftplib import FTP
from ftplib import all_errors as FTP_ERRORS
import os
import random
import tempfile
import subprocess
import collections
from datetime import datetime

import settings

class Master:

    def __init__(self, address = settings.MASTER_ADDRESS, port = settings.MASTER_PORT, timeout = settings.FTP_CONNECT_TIMEOUT_SECS):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.connect_attempts = 0
        # Make sure the line below is indented properly
        worker_dirs = """worker-bc37d5f8-a296-4e8b-adb0-dc15be9a16fd
worker-40d37e2d-cd2a-4fc1-8919-2de74a68256a
worker-1885f939-8c3d-450e-aee0-3796c1c2cc07""".split('\n')
        self.dirs = collections.deque(worker_dirs)

    def warn(self, w):

        filename_prefix = '{}_{}'.format(os.uname()[1],
                datetime.utcnow().strftime("%y-%m-%d-%H:%M:%S"))

        # error file
        # TODO: add some info such as exception to contents of this file
        error_filename = os.path.join(settings.ROOT, 'datamill_error')
        open(error_filename, 'w').close() # touch

        self.upload(error_filename, settings.ERROR_DIR,
            '{}_{}'.format(filename_prefix, os.path.basename(error_filename)))

        for k, f in w.status_file_dict().items():
            if os.path.exists(f):
                self.upload(f, settings.ERROR_DIR,
                        '{}_{}'.format(filename_prefix, k))

        commands_to_upload = [ 'dmesg', 'df', 'mount', 'ifconfig' ]

        for cmd in commands_to_upload:
            local_filename = os.path.join(settings.ROOT, '{}_output'.format(cmd))
            with open(local_filename, 'w') as f:
                subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, shell=True)

            self.upload(local_filename, settings.ERROR_DIR,
                    '{}_{}'.format(filename_prefix, os.path.basename(local_filename)))

        for filename in [settings.STDERR_LOG, settings.CONTROLLER_STDOUT_LOG]:
            file = os.path.join(settings.ROOT, settings.WORKER_LOG_DIR, filename)
            if os.path.isfile(file):
                self.upload(file, settings.ERROR_DIR, '{}_{}'.format(filename_prefix, filename))

    def connect(self):
        self.ftp = FTP()
        try:
            self.connect_attempts += 1
            self.ftp.connect(self.address, self.port, self.timeout)
        except FTP_ERRORS, e:
            self.ftp.close()
            if self.connect_attempts < 10:
                self.connect()
                return
        else:
            self.ftp.login()
        self.connect_attempts = 0

    def quit(self):
        self.ftp.quit()

    @classmethod
    def worker_ftp_dir(cls, worker):
        # this is here and not in worker.py because it only exists in ftp-based
        # implementations of datamill
        return 'worker-{}'.format(worker.uuid())

    def upload(self, local_file, remote_dir, remote_file):
        # takes care of integrity
        self.connect()

        self.ftp.cwd('/{}'.format(remote_dir)) # extra slashes don't hurt

        with open(local_file, 'rb') as f:
            self.ftp.storbinary('STOR {}'.format(os.path.basename(remote_file)), f)

        self.quit()

    def download(self, remote_dir, remote_file, local_file):
        # takes care of integrity
        self.connect()
        remote_hashfile = '{}.md5'.format(remote_file)
        local_hashfile = '{}.md5'.format(local_file)
        self.ftp.cwd(remote_dir)
        self.ftp.retrbinary('RETR {}'.format(remote_file),
                open(local_file, 'wb').write)
        self.ftp.retrbinary('RETR {}'.format(remote_hashfile),
                open(local_hashfile, 'wb').write)

        self.quit()

    def register(self, worker):
        self.upload(os.path.join(settings.ROOT, worker.hello_file()), settings.HELLO_DIR,
                '{}v{}r{}{}'.format(worker.uuid(), worker.hello_version(), worker.hardware_revision(), settings.HELLO_EXTENSION))

    def update_ip(self, worker):
        self.upload(os.path.join(settings.ROOT, worker.ip_file()), settings.IP_UPDATE_DIR,
                '{}{}'.format(worker.uuid(), settings.IP_EXTENSION))

    def get_dir(self):
        self.dirs.rotate(1)
        return self.dirs[0]

    def pick_job(self):
        self.connect()
        self.ftp.cwd(self.get_dir())
        ftp_list = self.ftp.nlst()
        self.quit()

        packages = [f.rpartition(settings.PACKAGE_EXTENSION)[0]
                for f in ftp_list if f.endswith(settings.PACKAGE_EXTENSION)]

        # get the dones and wips, removing their extensions
        dones = [f.rpartition(settings.DONE_EXTENSION)[0]
                for f in ftp_list if f.endswith(settings.DONE_EXTENSION)]
        wips  = [f.rpartition(settings.WIP_EXTENSION)[0]
                for f in ftp_list if f.endswith(settings.WIP_EXTENSION)]

        # remove the dones and wips from the job candidates
        packages = list(set(packages) - set(dones) - set(wips))

        if len(packages) == 0:
            return None

        # get package basenames (nlst returns full path, unlike os.listdir)
        packages = map(os.path.basename, packages)

        # sort packages by prio (which is alphabetical)
        packages.sort()

        priority = packages[0].split('-')[0].strip()

        # take just the highest prio packages (match 1st two chars)
        packages = [f for f in packages if f.split('-')[0].strip() == priority]

        # pick a package at random from highest prio
        # we pick at random in case one experiment generates a million 01-aaa.tar.gz
        # and another generates one 01-zzz.tar.gz
        return random.choice(packages)

    def get_job(self, worker):
        target = self.pick_job(worker)

        if not target:
            return None

        target_file = '{}{}'.format(target, settings.PACKAGE_EXTENSION)
        target_conf_file = '{}{}'.format(target, settings.CONF_EXTENSION)
        tmpdir = tempfile.mkdtemp()

        for f in [ target_file, target_conf_file ]:
            self.download(Master.worker_ftp_dir(worker), f, os.path.join(tmpdir, f))

    @classmethod
    def job_name_from_filename(cls, filename):
        return os.path.basename(filename).partition('.')[0]

    def put_wip(self, worker, job):
        # This is the path on the ftp side, so it must have a literal '/'
        dst_dir = os.path.join('/', Master.worker_ftp_dir(worker))
        dst_wip_filename = '{}{}'.format(job.name(), settings.WIP_EXTENSION)

        # touch a temp wip
        wip_fd, local_wip_file = tempfile.mkstemp()
        os.close(wip_fd)
        self.upload(local_wip_file, dst_dir, dst_wip_filename)

    def put_job(self, worker, job):

        dst_dir = os.path.join('/', Master.worker_ftp_dir(worker))
        dst_done_filename = '{}{}'.format(job.name(), settings.DONE_EXTENSION)

        # upload the actual data results, if they exist
        for k, f in dict(worker.status_file_dict().items() +
                job.results_file_dict().items()).items():
            if os.path.exists(f) and os.path.isfile(f):
                # In this case the . in {}.{} is required
                remote_filename = '{}.{}'.format(job.name(), k)
                self.upload(f, dst_dir, remote_filename)

        # touch a temp done
        done_fd, local_done_file = tempfile.mkstemp()
        os.close(done_fd)
        self.upload(local_done_file, dst_dir, dst_done_filename)
