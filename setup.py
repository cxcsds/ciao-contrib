"""
Create the CIAO contributed package. Options include:

  --version=4.13.0

"""

import glob
import sys

from distutils.core import setup

def list_files(pattern):
    "Return the giles in a directory, in a sorted list"
    return sorted(glob.glob(pattern))


VERSION="4.13.0"
for val in sys.argv:
    if val.startswith("--version="):
        VERSION = val.split("=")[1]
        sys.argv.remove(val)
        break


scripts = list_files("bin/*")
params = list_files("param/*.par")
docs = list_files("share/doc/xml/*.xml")
datum = list_files("data/*")
configs = list_files("config/*")
# etc = list_files("etc/conda/activate.d/*")

data_files = [("param", params),
              ("share/doc/xml", docs),
              ("config", configs),
              ("data", datum),
              (".", ["Changes.CIAO_scripts", "README_CIAO_scripts"])
]

mods = [ "ciao_contrib",
    "ciao_contrib/region",
    "ciao_contrib/_tools",
    "ciao_contrib/cda",
    "coords",
    "crates_contrib",
    "dax",
    "sherpa_contrib",
    "sherpa_contrib/profiles",
    "sherpa_contrib/tests",
    "sherpa_contrib/xspec"]

setup(name='ciao-contrib',
      version=VERSION,
      license='GNU GPL v3',
      description='CIAO Contributed scripts',
      author='CXCSDS and Friends',
      author_email='cxchelp@cfa.harvard.edu',
      url='https://github.com/cxcsds/ciao-contrib/',
      scripts=scripts,

      # Note that data_files is deprecated
      data_files=data_files,

      packages=mods,
      py_modules=["lightcurves",]
)
