
import glob
import os
import sys

scripts = sorted( glob.glob( "bin/*"))
params = sorted(glob.glob("param/*.par"))
docs = sorted(glob.glob("share/doc/xml/*.xml"))
datum = sorted(glob.glob("data/*"))
configs = sorted(glob.glob("config/*"))
etc = sorted(glob.glob("etc/conda/activate.d/*"))

VERSION="4.13.0"
for val in sys.argv:
    if val.startswith("--version="):
        VERSION = val.split("=")[1]
        sys.argv.remove(val)
        break


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


from distutils.core import setup
setup( name='ciao-contrib',
        version=VERSION,
        license='GNU GPL v3',
        description='CIAO Contributed scripts',
        author='CXCSDS and Friends',
        author_email='cxchelp@cfa.harvard.edu',
        url='https://github.com/cxcsds/ciao-contrib/',
        scripts = scripts,
        data_files = [ ("param", params ),
                       ("share/doc/xml", docs ),
                       ("config", configs),
                       ("data", datum),
                       (".", ["Changes.CIAO_scripts", "README_CIAO_scripts"]),
                       ],
        packages=mods,
        py_modules=["lightcurves",]
        )
