"""
Create the CIAO contributed package. Options include:

  --version=4.16.0

"""

import glob
import sys

from setuptools import setup


def list_files(pattern):
    "Return the giles in a directory, in a sorted list"
    files = glob.glob(pattern)

    # Remove *~ files (any other ones?) Could restrict to
    # files stored in git?
    #
    files = [f for f in files if not (f.endswith('~') or f.startswith('flycheck_'))]

    if files == []:
        raise ValueError(f"No match for pattern: {pattern}")

    return sorted(files)


VERSION = "4.16.0"
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
              ("config", list_files("config/*")),
              ("data", list_files("data/*")),
              (".", ["Changes.CIAO_scripts"])
]

setup(version=VERSION,
      scripts=scripts,

      # Note that data_files is deprecated
      data_files=data_files,
)
