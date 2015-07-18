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
        worker_dirs = """worker-02ed23ef-c072-463a-ba53-2aace5dedfe4
worker-0eb0d755-ce18-4913-9e2b-e6dd0f0884c5
worker-11111111-2222-3333-4444-555555555555
worker-1885f939-8c3d-450e-aee0-3796c1c2cc07
worker-19cd6f90-eb5f-427c-82d7-1a626bc9a61c
worker-2182f593-8cc7-4bcd-adb4-c87d4f9d8e0a
worker-28186a29-7117-48bc-8504-84d8febe01fa
worker-36dc1424-8197-4816-98c5-7498ade38278
worker-40d37e2d-cd2a-4fc1-8919-2de74a68256a
worker-45d22379-e2c0-4654-bcfc-cbdd901c50fd
worker-490e880f-aba6-4cd9-b56e-005820693730
worker-59de5631-0e10-4637-a9a8-e26d3110dc77
worker-5fd218f7-bc07-481b-a5f8-4c01721a6422
worker-665f1348-96bb-42da-b1b4-b51a332381f5
worker-854bab83-5835-4d91-a199-97a09a1d5eb2
worker-97d6dab5-8d51-4b78-8135-4e6d23f2d0e3
worker-9a3ec806-b16f-4dae-af0b-7d21c557ca45
worker-9b3d610e-c7ac-4d9d-896c-a6f68ca11fa3
worker-9ca9a1af-9d90-4671-bc58-dc585213188a
worker-a3c6dc0e-ece8-4a22-8b91-76b7ed3156f5
worker-a4976a58-6a09-4f06-b44b-52be6ba8ad69
worker-aa095bec-47a2-4247-98ed-5ae2fc76c2d5
worker-b283f840-e889-4854-9df5-bdda1b93d416
worker-bc37d5f8-a296-4e8b-adb0-dc15be9a16fd
worker-c02946d7-887c-4f3b-9337-1d9420ba9b8d
worker-c7b8aaca-9998-45c4-8fe1-0fe6e3bed168
worker-cd65c9ac-ab08-4202-875c-8494e0f00c26
worker-d4618698-ae18-4f94-940f-7311e507fff6
worker-defeb3df-bffa-4607-a757-60980eac3453
worker-e75f647d-fcd8-451e-8b46-ef6073347da5
worker-eb986072-4ad4-44e2-a90a-978a24745360
worker-edf8f502-68f2-4a53-bdba-c639716b77ad
worker-f237af03-ae12-43d7-aa99-72bd6000219a
worker-f263abb6-ef7d-4cc6-88b5-53cd3460d16c
worker-fa7e247b-f971-4b11-8f46-6b83dec13094
worker-faecd71b-3127-48c7-8cf6-a6996ba07c32""".split('\n')
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
