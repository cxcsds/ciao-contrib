
This is the repository used to create the CIAO contributed script
package. This is an experimental repository; in other words we
reserve the right to stop using it at any time.

# Aim

The CIAO contributed script package provides additional scripts,
Python modules, and helper files to extend the capabilities of the
CIAO software system available at https://cxc.harvard.edu/ciao/. The
script package is distributed as part of the CIAO installation and
is derived from the code in this repository. This repository is
intended for development of the CIAO contrib package, and it
*should not* be used for scientific analysis. In other words, do
not use this version; instead, use the version that comes with CIAO!

# License

The CIAO contributed software is released for use under the GNU
General Public License (GPL) Version 3 (or at your option any later
version). The terms of the GNU General Public License are described
in the COPYING file in the root directory of the $ASCDS_INSTALL tree
or of this repository.

The contributed script package also contains code released by the
High Energy Astrophysics Science Archive Research Center (HEASARC)
of NASA as part of the HEASoft software package, available from
https://heasarc.nasa.gov/lheasoft/ These files are located in
`ciao-<version>/contrib/share/xspec/` and are released with the
same conditions as HEASoft (which we believe to be the Public Domain).

# Issues

It might be preferrable to use distutils (`setup.py`) to create the
Python package, rather than the current system, but that depends on
how it plays with the CIAO installation system.

Tests are not included in this repository. Some will be added, but
regression tests may not be (as they can take time to run, require
a lot of data, and may rely on unreleased versions of CIAO).

# Tasks

## How to create a tarball for the CIAO CM team

A) a development release

    % ./mk_script_tarfile 4.12 dev

will create the file

    ciao-4.12-contrib-DEV.tar.gz

with a version file that looks like

    % cat ciao-4.12/contrib/VERSION.CIAO_scripts 
    scripts 4.12.DEV Friday, December 12, 2014

B) a release candidate

    % ./mk_script_tarfile 4.12 2

will create the file

    ciao-4.12-contrib-2.tar.gz

with a version file that looks like

    % cat ciao-4.12/contrib/VERSION.CIAO_scripts 
    scripts 4.12.2 Friday, December 12, 2014

At present there is no system to automatically look up the version
number.

## Updating the runtool module

The `./mk_runtool.py` command is used to create the ciao_contrib.runtool
module, and uses

    mk_runtool.header
    mk_runtool.footer

which should not be edited unless you know what you're doing, and the
contents of

    $ASCDS_INSTALL/param
    $ASCDS_INSTALL/bin

    ciao-<version>/contrib/param
    ciao-<version>/contrib/bin

That is, it builds the runtool module for the configured CIAO and the
contents of this repository. That means that if you have updated a
parameter file, or added a new tool, that you have to copy it into
this repository *before* running mk_runtool.py.

**NOTE** you do not have to check in these files, so you can copy the
changes in, run `mk_runtool` to create a new module that you can use
for testing, without changing the repository.

An example run:

    % ./mk_runtool.py
    Input directores:
      /proj/xena/ciaot_install/osx64.131202/ciao-4.7
      ciao-4.7/contrib
   
    Note: converting AXAF_HRC-I_QE_FILE -> AXAF_HRC_I_QE_FILE
    Note: converting AXAF_HRC-I_QEU_FILE -> AXAF_HRC_I_QEU_FILE
    ...
    WARNING: parameter name is not a valid Python identifier and does not transform '-' -> '_': 3,s,h,"111",,,
    WARNING: parameter name is not a valid Python identifier and does not transform '-' -> '_': 5,s,h,"11111",,,
    ...
    Note: converting cmy-cyan -> cmy_cyan
    ...
    Note: minval/maxval is INDEF in
      xoffset,i,h,INDEF,INDEF,INDEF,"celldetect offset of x axis from optical axis"
    Note: minval/maxval is INDEF in
      yoffset,i,h,INDEF,INDEF,INDEF,"celldetect offset of y axis from optical axis"
   
    Created: ciao-4.7/contrib/lib/python2.7/site-packages/ciao_contrib/runtool.py

The first lines tell you where it is looking for the tools and
parameter files, then come notes and warnings from processing the
parameter files ("-" characters get renamed to "_" and some parameters
are still not valid after this transformation and so are skipped, this
could be improved but for now I have not bothered). The last two lines
are just to remind Doug that he really needs to look at the INDEF
handling for min/max values.

## The CIAO versions file

The `make_versions_file` should be started after CIAO has been set up, and
returns the versions of the various packages needed for the
`check_ciao_version` script. It should be run something like

    % ./make_versions_file
    CIAO CIAO 4.6 Monday, December  2, 2013
    chips chips 4.6.1 Monday, December  2, 2013
    core core 4.6.1 Monday, December  2, 2013
    graphics graphics 4.6.1 Monday, December 2, 2013
    obsvis obsvis 4.6.1 Monday, December  2, 2013
    prism prism 4.6.1 Monday, December  2, 2013
    sherpa sherpa 4.6.1 Monday, December  2, 2013
    tools tools 4.6.1 Monday, December  2, 2013
    contrib scripts 4.6.1 Thursday, December 12, 2013
    % ./make_versions_file > ciao_versions.dat

and then `ciao_versions.dat` copied to the correct location on the web
site.

If there is the need to create system-specific versions, then
make sure the script is run using that version and create a
file called `ciao_versions.<system>.dat`, where `<system>` matches
the names used internally (e.g. `Linux64` or `osxSierraP3`); that is,
the contents of the file `$ASCDS_INSTALL/ciao-type`. The case is
important!

NOTE: at present it does not use the version of the contrib file in the
      `ciao-<version>/contrib/VERSION.CIAO_scripts` file, but uses the
      version in $ASCDS_INSTALL. This is messy, but can be hand
      edited for now.
