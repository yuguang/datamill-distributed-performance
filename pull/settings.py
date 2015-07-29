import os

# BOTH-SIDE SETTINGS
DATAMILL_DIR = 'datamill'
WORKER_LOG_DIR = 'tmp'
ROOT = '/'

PACKAGE_EXTENSION = '.tar.gz'
DONE_EXTENSION = '.done'
INTEG_EXTENSION = '.md5'
WIP_EXTENSION = '.wip'
CONF_EXTENSION = '.json'
HELLO_EXTENSION = '.json'
UUID_EXTENSION = '.json'
IP_EXTENSION = HELLO_EXTENSION

# PORTAGE FILE PATHS
PORTAGE_DIR = os.path.join('etc', 'portage')
PORTAGE_ENV_DIR = os.path.join(PORTAGE_DIR, 'env')
PORTAGE_PKG_ENV_DIR = os.path.join(PORTAGE_DIR, 'package.env')
PORTAGE_KEYWORD_DIR = os.path.join(PORTAGE_DIR, 'package.keywords')
PORTAGE_USE_DIR = os.path.join(PORTAGE_DIR, 'package.use')

# LIST OF ALL PORTAGE SUB DIRS WE TOUCH
#
# We need this so that we can iterate over it and clean up portage
# configs if they exist on the machine as a result of user
# installation.
PORTAGE_DIRS = [
    PORTAGE_ENV_DIR,
    PORTAGE_PKG_ENV_DIR,
    PORTAGE_KEYWORD_DIR,
    PORTAGE_USE_DIR,
]

# DATAMILL SPECIFIC PORTAGE FILES
DATAMILL_PORTAGE_CONF = os.path.join(PORTAGE_DIR, 'datamill_portage_config')
DATAMILL_KEYWORD_CONF = os.path.join(PORTAGE_KEYWORD_DIR, 'datamill.keywords')
DATAMILL_ENV_CONF = os.path.join(PORTAGE_PKG_ENV_DIR, 'datamill.env')
DATAMILL_USE_CONF = os.path.join(PORTAGE_USE_DIR, 'datamill.use')

# CONTROLLER SIDE SETTINGS
MASTER_ADDRESS = 'mini.resl.uwaterloo.ca'
MASTER_PORT = 2121
ERROR_DIR = 'worker-errors'
HELLO_DIR = 'worker-new'
IP_UPDATE_DIR = 'worker-ip'
BENCHMARK_MOUNT = 'mnt/benchmark'
HELLO_FILENAME = os.path.join(DATAMILL_DIR, 'hello{}'.format(HELLO_EXTENSION))
UUID_FILENAME = os.path.join(DATAMILL_DIR, 'uuid{}'.format(UUID_EXTENSION))
IP_FILENAME = os.path.join(DATAMILL_DIR, 'ip{}'.format(HELLO_EXTENSION))
WORKER_UUID = None
WORKER_TIMEOUT_DAYS = 2
CONTROLLER_LOOP_SLEEP_TIME = 5 # SECS
BENCHMARK_BACKUP = os.path.join(DATAMILL_DIR, 'backups', 'backup.tar.gz')
BACKUP_INSUFFICIENT_SPACE_PERCENT = 30 # leave extra free space on arm boards
LAYMAN_TIMEOUT_SECS = 30
LAYMAN_BACKOFF_SECS = 15
LAYMAN_RETRIES = 5
FTP_CONNECT_TIMEOUT_SECS = 10
DATAMILL_COLLECTOR_LOOP_SECS=60
STDERR_LOG = 'stderr.log'
CONTROLLER_STDOUT_LOG = 'controller_stdout.log'

# PORTAGE SPECIFIC VARIABLES
#
# Without exception, each item in this dictionary is a file associated
# with what will be its contents.
CONTROLLER_PORTAGE_CONFIG = {
    DATAMILL_PORTAGE_CONF: """
# DATAMILL MAKE CONF EDITS
WORKER_USEFLAGS="-X -cups -gtk -cairo -alsa"
USE="$USE $WORKER_USEFLAGS"
""",

    os.path.join(PORTAGE_ENV_DIR, 'clang-env'): """
# use only one thread to keep resource demands low
MAKEOPTS="-j1"
""",

    DATAMILL_ENV_CONF: """
# DataMill package specific environments
sys-devel/llvm clang-env
sys-devel/clang clang-env
""",

    DATAMILL_USE_CONF: """
# DataMill useflags
sys-devel/llvm clang
""",
}


# BENCHMARK SIDE SETTINGS
JOB_STATUS_FILE = 'job_status'
WORKER_STATUS_FILE = 'worker_status'
BENCHMARK_WORK_DIR = os.path.join(DATAMILL_DIR, 'work')
BENCHMARK_TIME_LIMIT_HOURS = 24
STANDARD_PACKAGE_FILENAME = 'user_package.tar.gz'
STANDARD_CONFIGURATION_FILENAME = 'user_package.json'

BENCHMARK_PORTAGE_CONFIG = dict(CONTROLLER_PORTAGE_CONFIG.items() + {

    DATAMILL_KEYWORD_CONF: """
# DataMill Keywords
=sys-devel/llvm-3.3
=sys-devel/clang-3.3
dev-util/perf
""",

}.items())

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s:%(message)s',
            'datefmt': '%m/%d/%Y %I-%M-%S%p',
        },
    },
    'handlers': {
        'datamill_controller_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, WORKER_LOG_DIR, 'controller.log'),
            'formatter': 'verbose',
        },
        'datamill_benchmark_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, WORKER_LOG_DIR, 'benchmark.log'),
            'formatter': 'verbose',
        },
        'datamill_common_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, WORKER_LOG_DIR, 'datamill_common.log'),
            'formatter': 'verbose',
        },
        'watchdog_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, WORKER_LOG_DIR, 'watchdog.log'),
            'formatter': 'verbose',
        },
        'datamill_test_logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(ROOT, WORKER_LOG_DIR, 'datamill_test.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'controller': {
            'handlers': ['datamill_controller_logfile', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'benchmark': {
            'handlers': ['datamill_benchmark_logfile', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'worker_common': {
            'handlers': ['datamill_common_logfile'],
            'propagate': True,
            'level': 'INFO',
        },
        'watchdog': {
            'handlers': ['watchdog_logfile', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'test': {
            'handlers': ['datamill_test_logfile'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

try:
    from worker_common.virtual_worker_settings import *
except ImportError:
    pass

try:
    from worker_common.local_settings import *
except ImportError:
    pass
