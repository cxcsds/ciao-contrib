"""
Create the CIAO contributed package. Options include:

  --version=4.13.0

"""

import glob
import sys

from distutils.core import setup

def list_files(pattern):
    "Return the giles in a directory, in a sorted list"
    files = glob.glob(pattern)

    # Remove *~ files (any other ones?) Could restrict to
    # files stored in git?
    #
    files = [f for f in files if not f.endswith('~')]

    if files == []:
        raise ValueError(f"No match for pattern: {pattern}")

    return sorted(files)


VERSION="4.13.0"
for val in sys.argv:
    if val.startswith("--version="):
        VERSION = val.split("=")[1]
        sys.argv.remove(val)
        break


scripts = list_files("bin/*")

# etc = list_files("etc/conda/activate.d/*")

data_files = [("param", list_files("param/*.par")),
              ("share/doc/xml", list_files("share/doc/xml/*.xml")),
              ("config", list_files("config/*")),
              ("data", list_files("data/*")),
              (".", ["Changes.CIAO_scripts", "README_CIAO_scripts"])
]

# The XSPEC include files contains a number of sub-directories.
# We can hard-code this list at the cost of having to modify this
# code when there's a change.
#
# These header files are from a Linux installation. Hopefully they
# are platform agnostic.
#
for dname in ["install", "install/readline",
              "install/wcslib", "install/CCfits",
              "install/ape", "install/fftw",
              "builddir/XSFit/FitMethod/Unimplemented/Anneal",
              "builddir/XSFit/FitMethod/Unimplemented/Genetic",
              "builddir/XSFit/FitMethod/LevMarq",
              "builddir/XSFit/FitMethod/Minuit",
              "builddir/XSFit/FitMethod/Minuit/minuit2/inc/Math",
              "builddir/XSFit/FitMethod/Minuit/minuit2/inc/Minuit2",
              "builddir/XSFit/FitMethod/Minuit/minuit2/test/MnSim",
              "builddir/XSFit/FitMethod/Minuit/minuit2/test/MnTutorial",
              "builddir/XSFit/FitMethod/Minuit/minuit2/src",
              "builddir/XSFit/StatMethod/EDF",
              "builddir/XSFit/StatMethod/Cstat",
              "builddir/XSFit/StatMethod/Runs",
              "builddir/XSFit/StatMethod/ChiSquare",
              "builddir/XSFit/MCMC",
              "builddir/XSFit/Randomizer",
              "builddir/XSFit/Fit",
              "builddir/tools/cxsetup",
              "builddir/tools/initpackage",
              "builddir/tools/include",
              "builddir/XSUtil/Parse",
              "builddir/XSUtil/Error",
              "builddir/XSUtil/Utils",
              "builddir/XSUtil/Numerics",
              "builddir/XSUtil/Signals",
              "builddir/XSUser/Global",
              "builddir/XSUser/Handler",
              "builddir/XSUser/Python/xspec",
              "builddir/XSUser/Help",
              "builddir/XSUser/UserInterface",
              "builddir/include",
              "builddir/XSFunctions",
              "builddir/XSFunctions/Utilities",
              "builddir/XSModel/Model",
              "builddir/XSModel/Model/MixFunction",
              "builddir/XSModel/Model/EmissionLines",
              "builddir/XSModel/Model/Component",
              "builddir/XSModel/Model/Component/OGIPTable",
              "builddir/XSModel/GlobalContainer",
              "builddir/XSModel/Data",
              "builddir/XSModel/Data/Detector",
              "builddir/XSModel/Data/BackCorr",
              "builddir/XSModel/DataFactory",
              "builddir/XSModel/Parameter",
              "builddir/XSPlot/Commands",
              "builddir/XSPlot/Plt",
              "builddir/XSPlot/Plot",
              "builddir/xslib",
              "builddir/xslib/ihf"]:

    outdir = f"share/xspec/{dname}"
    data_files.append((outdir, list_files(outdir + "/*.h")))


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
