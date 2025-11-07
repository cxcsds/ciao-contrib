"""
Create the CIAO contributed package. Options include:

  --version=4.18.0

"""

import glob
import sys
import os

from setuptools import setup


def list_files(pattern):
    "Return the giles in a directory, in a sorted list"
    files = glob.glob(pattern)

    # Remove *~ files (any other ones?) Could restrict to
    # files stored in git?
    #
    files = [f for f in files if not (f.endswith('~') or f.startswith('flycheck_'))]

    # Remove sub-directories
    #
    #
    files = [f for f in files if not os.path.isdir(f)]

    if files == []:
        raise ValueError(f"No match for pattern: {pattern}")

    return sorted(files)


VERSION = "4.18.0"
for val in sys.argv:
    if val.startswith("--version="):
        VERSION = val.split("=")[1]
        sys.argv.remove(val)
        break


scripts = list_files("bin/*")

# etc = list_files("etc/conda/activate.d/*")

data_files = [("param", list_files("param/*.par")),
              ("share/doc/xml", list_files("share/doc/xml/*.xml")),
              ("share/xspec/install", list_files("share/xspec/install/*cxx")),
              ("share/sherpa/notebooks", list_files("share/sherpa/notebooks/*ipynb")),
              ("config", list_files("config/*")),
              ("data", list_files("data/*")),
              ("data/ebounds-lut", list_files("data/ebounds-lut/*")),
              (".", ["Changes.CIAO_scripts"])
]

setup(version=VERSION,
      scripts=scripts,

      # Note that data_files is deprecated
      data_files=data_files,
)
