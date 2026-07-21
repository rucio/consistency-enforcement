import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), "r").read()

def get_version():
    g = {}
    exec(open(os.path.join("rucio_consistency", "version.py"), "r").read(), g)
    return g["Version"]

setup(
    name = "rucio-consistency",
    version = get_version(),
    # The original author of most of this is the late Igor Mandrichenko of Fermilab. Vaandering is the author of record
    author = "Eric Vaandering",
    author_email = "ewv@fnal.gov",
    description ="Common modules and scripts for Rucio consistency enforcement",
    license = "BSD 3-clause",
    url = "https://github.com/rucio/consistency-enforcement",
    packages=['rucio_consistency', "rucio_consistency.scripts", "rucio_consistency.xrootd", "rucio_consistency.davs"],
    long_description="Common modules and scripts for Rucio consistency enforcement", #read('README'),
    zip_safe = False,
    install_requires=["sqlalchemy", "pythreader"],
    entry_points = {
        "console_scripts": [
            "rce_update_stats = rucio_consistency.scripts.update_stats:main",
            "rce_partition = rucio_consistency.scripts.partition:main",
            "rce_db_dump = rucio_consistency.scripts.db_dump:main",
            "rce_cmp5 = rucio_consistency.scripts.cmp5:main",
            "rce_cmp3 = rucio_consistency.scripts.cmp3:main",
            "rce_cmp2 = rucio_consistency.scripts.cmp2:main",
            "rce_scan = rucio_consistency.xrootd.xrootd_scanner:main",
            "rce_davs_scan = rucio_consistency.davs.davs_scanner:main"
        ]
    }
)
