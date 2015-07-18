import os
import portage
import subprocess
import time
from datetime import datetime
import settings
import logging as logger

class Emerge(object):

    @classmethod
    def worker_needs_update(cls):

        cls.layman_sync()
        if portage.pkgcmp(portage.pkgsplit(cls.installed_package_atom("sys-apps/datamill-controller")),
                          portage.pkgsplit(cls.available_package_atom("sys-apps/datamill-controller"))) != 0:
            return True
        else:
            return False

    @classmethod
    def installed_package_atom(cls, pattern):
        """
        Returns a string in the standard gentoo cpv (category package version) format:

        <category>/<package>-<version>

        Returns None if no package is found.
        """

        # Vartree stores all the installed packages
        dbapi = portage.db[portage.root]['vartree'].dbapi
        installed_versions = dbapi.match(pattern)

        if len(installed_versions) > 1:
            logger.warning("More than one copy of {} installed??".format(pattern))
        elif len(installed_versions) == 0:
            return None

        # Returns Gentoo cpv package name
        return installed_versions[0]

    @classmethod
    def version_string_from_atom(cls, atom):
        return "-".join(portage.pkgsplit(atom)[1:])

    @classmethod
    def installed_package_version(cls, pattern):
        return cls.version_string_from_atom(cls.installed_package_atom(pattern))

    @classmethod
    def update_controller_package(cls, pattern="sys-apps/datamill-controller"):
        """Updates the controller side. Uses only the portage configuration
        located on the controller side for updates.
        Doesn't sync layman

        """

        controller_atom = cls.available_package_atom(pattern)
        logger.info("Updating {} on controller side".format(pattern))
        lines = subprocess.check_output("emerge ={} --update".format(controller_atom),
                                        stderr=subprocess.STDOUT, shell=True)
        logger.info("emerge return: {}".format(lines))

    @classmethod
    def update_benchmark_package(cls, pattern="sys-apps/datamill-benchmark"):
        """Installs the benchmark software. Uses only the portage
        configuration located on the benchmark side for updates.

        All benchmark side package updates are kept in a binary
        package cache (controller side) which should be periodically
        cleared out.

        """

        benchmark_atom = cls.available_package_atom(pattern)

        logger.info("Updating {} on benchmark side".format(pattern))

        # installs from controller's cache to reduce build time
        lines = subprocess.check_output("emerge ={package_atom} --update --buildpkg --usepkg --binpkg-respect-use --root={root} --config-root={config_root}"\
                                        .format(
                                            package_atom = benchmark_atom,
                                            root         = os.path.join(settings.ROOT, settings.BENCHMARK_MOUNT),
                                            config_root  = os.path.join(settings.ROOT, settings.BENCHMARK_MOUNT)
                                        ), stderr=subprocess.STDOUT, shell=True)

        logger.info("emerge output: {}".format(lines))

    @classmethod
    def available_package_atom(cls, pattern):

        """This function returns the newest package found for the given
        category/package pattern

        This function calls layman to sync the datamill overlay if the
        sync keyword argument is set to true.

        Returns a string in the standard gentoo cpv (category package version) format:

        <category>/<package>-<version>

        Returns None if no package is found.

        """

        # Porttree stores all the available packages
        dbapi = portage.db[portage.root]['porttree'].dbapi
        available_versions = dbapi.match(pattern)

        if len(available_versions) == 0:
            return None
        else:
            # split packages into comparable format, get newest, join
            # with '-' for the valid package atom of newest.
            return "-".join(sorted(map(portage.pkgsplit, available_versions), cmp=portage.pkgcmp)[-1])

    @classmethod
    def available_package_version(cls, pattern):
        return cls.version_string_from_atom(cls.available_package_atom(pattern))

    @classmethod
    def layman_sync(cls):
        """Call layman to sync the datamill overlay.

        Network faults can cause some pretty significant damage since errors
        here cause a full worker wipe, plus lost results.

        We have retries and backoff time to try and combat this.

        """

        retries = 0
        r = None

        # Explicit limit to whileloop
        while retries < settings.LAYMAN_RETRIES:

            retries = retries + 1
            try:
                cls._layman_sync_call()
                break
            except:
                if retries >= settings.LAYMAN_RETRIES:
                    raise
                logger.warning("layman -S failed, backing off for {} seconds and retrying".format(
                    settings.LAYMAN_BACKOFF_SECS
                ))
                time.sleep(settings.LAYMAN_BACKOFF_SECS)

    @classmethod
    def _layman_sync_call(cls):


        # This calls layman asynchronously and then polls to check
        # when it's done. An obscure and rare bug in layman causes it
        # to hang in the event of network problems. From that point
        # forward, layman will never return. As a result, we need to
        # busy-wait on layman and kill it if it's taking too long.
        #
        # In the future, if this strategy needs to change, ensure that
        # either layman no longer has this bug, or ensure that the
        # method used is robust to a hanging process.

        logger.info("Executing layman -S")

        start_time = datetime.now()
        layman_proc = subprocess.Popen("layman -S", shell = True)

        while layman_proc.poll() is None:

            current_time = datetime.now()
            if (current_time - start_time).seconds > settings.LAYMAN_TIMEOUT_SECS:
                layman_proc.kill()
                raise OSError("layman timeout")

            time.sleep(5)

        if layman_proc.returncode != 0:
            raise OSError("layman failed, returncode: {}".format(layman_proc.returncode))
