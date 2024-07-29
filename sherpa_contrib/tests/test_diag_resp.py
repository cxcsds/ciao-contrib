#
#  Copyright (C) 2024
#            Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

"""
Test routines for the diag_resp code
"""

from os import environ
from random import choice, randint, randrange, shuffle
from collections import namedtuple
import pytest

from sherpa.astro.io import backend

try:
    from sherpa.astro.io import crates_backend
    crates_status = True
except (ImportError,ModuleNotFoundError) as E:
    crates_status = False

try:
    from sherpa.astro.io import pyfits_backend
    astropy_status = True
except (ImportError,ModuleNotFoundError) as E:
    astropy_status = False

from sherpa_contrib.diag_resp import mkdiagresp, build_resp, EGrid, _get_random_string



def _quash_ethresh_warning(func):
    """
    return compound decorator for reused set of decorators
    """

    deco1 = pytest.mark.filterwarnings("ignore:.*ENERG_LO value < 0:UserWarning")
    deco2 = pytest.mark.filterwarnings("ignore:.*ENERG_HI < ENERG_LO:UserWarning")
    deco3 = pytest.mark.filterwarnings("ignore:.*has a non-monotonic.*array:UserWarning")
    deco4 = pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")

    return deco1(deco2(deco3(deco4(func))))



def _randomize_case(string: str = "") -> str:
    """
    return randomized case for a given alphabetical string
    """

    upper = string.upper()
    lower = string.lower()

    randomize = (choice(s) for s in zip(lower,upper))

    return "".join(randomize)



def _remove_random_char(string: str="") -> str:
    """
    return string with random character removed from the input string
    """

    char = list(string)
    _ = char.pop(randrange(len(char)))

    return "".join(char)



def _shuffle_string(string: str="") -> str:
    """
    return string with random character removed from the input string
    """

    char = list(string)
    shuffle(char)

    return "".join(char)



def _shuffle_or_pop_string(string):
    if string is None:
        return None

    condition = randint(0,2)

    if condition == 1:
        return _shuffle_string(string)
    if condition == 2:
        return _remove_random_char(string)
    return string



def _get_configstr(telescope:str, instrument:str, detector:str, chantype:str) -> str:
    inststr = f"{instrument:/>{len(instrument)+1}}" if instrument is not None else ""
    detstr = f"{detector:->{len(detector)+1}}" if detector is not None else ""
    chantypestr = f"{chantype:>{len(chantype)+1}}" if chantype is not None else ""

    return f"{telescope}{inststr}{detstr}{chantypestr}"



def _instrument_configs(fdict: dict) -> dict[tuple[namedtuple]]:
    instrument_config = namedtuple("instconfig", ["instrument","detector","instfilter","nchan","chantype"])

    fdict["Chandra"] = ( instrument_config("ACIS",None,None,None,"PI"),
                         instrument_config("ACIS",None,None,None,"PI"),
                         instrument_config("ACIS",None,None,None,"PHA_no-CTIcorr"),
                         instrument_config("HRC",None,None,None,"PI")
    )

    fdict["ASCA"] = ( instrument_config("GIS",None,None,None,None),
                      instrument_config("GIS",None,None,256,None),
                      instrument_config("GIS",None,None,128,None),
                      instrument_config("SIS0","CCD0",None,None,"PI"),
                      instrument_config("SIS0","CCD1",None,None,"PI"),
                      instrument_config("SIS0","CCD2",None,None,"PI"),
                      instrument_config("SIS0","CCD3",None,None,"PI"),
                      instrument_config("SIS1","CCD0",None,None,"PI"),
                      instrument_config("SIS1","CCD1",None,None,"PI"),
                      instrument_config("SIS1","CCD2",None,None,"PI"),
                      instrument_config("SIS1","CCD3",None,None,"PI"),
                      instrument_config("SIS0","CCD0",None,None,"PHA"),
                      instrument_config("SIS0","CCD1",None,None,"PHA"),
                      instrument_config("SIS0","CCD2",None,None,"PHA"),
                      instrument_config("SIS0","CCD3",None,None,"PHA"),
                      instrument_config("SIS1","CCD0",None,None,"PHA"),
                      instrument_config("SIS1","CCD1",None,None,"PHA"),
                      instrument_config("SIS1","CCD2",None,None,"PHA"),
                      instrument_config("SIS1","CCD3",None,None,"PHA"),
                      instrument_config("SIS0","CCD0",None,512,"PI"),
                      instrument_config("SIS0","CCD1",None,512,"PI"),
                      instrument_config("SIS0","CCD2",None,512,"PI"),
                      instrument_config("SIS0","CCD3",None,512,"PI"),
                      instrument_config("SIS1","CCD0",None,512,"PI"),
                      instrument_config("SIS1","CCD1",None,512,"PI"),
                      instrument_config("SIS1","CCD2",None,512,"PI"),
                      instrument_config("SIS1","CCD3",None,512,"PI"),
                      instrument_config("SIS0","CCD0",None,512,"PHA"),
                      instrument_config("SIS0","CCD1",None,512,"PHA"),
                      instrument_config("SIS0","CCD2",None,512,"PHA"),
                      instrument_config("SIS0","CCD3",None,512,"PHA"),
                      instrument_config("SIS1","CCD0",None,512,"PHA"),
                      instrument_config("SIS1","CCD1",None,512,"PHA"),
                      instrument_config("SIS1","CCD2",None,512,"PHA"),
                      instrument_config("SIS1","CCD3",None,512,"PHA")
    )


    # there's 'HXM1' and 'HXM2'
    fdict["calet"] = ( instrument_config("GGBM","HXM",None,None,"GAIN_HI"),
                       instrument_config("GGBM","HXM",None,None,"GAIN_LO"),
                       instrument_config("GGBM","HXM1",None,None,"GAIN_HI"),
                       instrument_config("GGBM","HXM2",None,None,"GAIN_HI"),
                       instrument_config("GGBM","SGM",None,None,"GAIN_HI"),
                       instrument_config("GGBM","SGM",None,None,"GAIN_LO")
    )


    fdict["cos-b"] = ( instrument_config("COS-B",None,None,None,None),
    )


    fdict["einsten"] = ( instrument_config("IPC",None,None,None,None),
                         instrument_config("SSS",None,None,None,None),
                         instrument_config("MPC",None,None,None,None),
                         instrument_config("HRI",None,None,None,None)
    )


    fdict["exosat"] = ( instrument_config("CMA",None,None,None,None),
    )


    fdict["halosat"] = ( instrument_config("SDD",None,None,None,None),
    )


    fdict["ixpe"] = ( instrument_config("GPD",None,None,None,None),
    )


    fdict["maxi"] = ( instrument_config("GSC",None,None,None,None),
    )


    fdict["nicer"] = ( instrument_config("XTI",None,None,None,None),
    )


    ### there's FPMA and FPMB
    fdict["NuSTAR"] = ( instrument_config("FPM",None,None,None,None),
                        instrument_config("FPMA",None,None,None,None),
                        instrument_config("FPMB",None,None,None,None)
    )


    fdict["ROSAT"] = ( instrument_config("PSPC",None,None,None,None),
                       instrument_config("PSPC",None,None,34,None)
    )


    fdict["RXTE"] = ( instrument_config("HEXTE","PWA",None,None,None),
                      instrument_config("HEXTE","PWB",None,None,None),
                      instrument_config("PCA",None,None,None,None),
                      instrument_config("PCA",None,None,6,None)
    )


    fdict["BeppoSAX"] = ( instrument_config("PDS",None,None,None,None),
                          instrument_config("PDS",None,None,128,None),
                          instrument_config("PDS",None,None,60,None),
                          instrument_config("HPGSPC",None,None,None,None),
                          instrument_config("LECS",None,None,None,None),
                          instrument_config("MECS","M1",None,None,None),
                          instrument_config("MECS","M2",None,None,None),
                          instrument_config("MECS","M3",None,None,None),
                          instrument_config("WFC1",None,None,None,None),
                          instrument_config("WFC2",None,None,None,None)
    )


    fdict["SRG"] = ( instrument_config("eROSITA",None,None,None,None),
    )


    fdict["Suzaku"] = ( instrument_config("XIS",None,None,None,None),
                        instrument_config("XRS",None,None,None,None),
                        instrument_config("HXD","WELL_PIN",None,None,None),
                        instrument_config("HXD","WELL_GSO",None,None,None)
    )


    fdict["Swift"] = ( instrument_config("BAT",None,None,None,None),
                       instrument_config("XRT",None,None,None,"PI"),
                       instrument_config("XRT",None,None,None,"PHA"),
                       instrument_config("UVOT",None,"B",None,None),
                       instrument_config("UVOT",None,"UVM2",None,None),
                       instrument_config("UVOT",None,"U",None,None),
                       instrument_config("UVOT",None,"V",None,None),
                       instrument_config("UVOT",None,"UVW1",None,None),
                       instrument_config("UVOT",None,"UVW2",None,None),
                       instrument_config("UVOT",None,"WHITE",None,None)
    )


    fdict["XMM"] = ( instrument_config("EPIC","MOS",None,None,"PI"),
                     instrument_config("EPIC","PN",None,None,"PI"),
                     instrument_config("EPIC","MOS1",None,None,"PHA"),
                     instrument_config("EPIC","MOS2",None,None,"PHA"),
                     instrument_config("EPIC","PN",None,None,"PHA"),
                     instrument_config("RGS",None,None,None,None)
    )


    fdict["XRISM"] = ( instrument_config("XTEND",None,None,None,None),
                       instrument_config("RESOLVE",None,None,None,"hi-res"),
                       instrument_config("RESOLVE",None,None,None,"mid-res"),
                       instrument_config("RESOLVE",None,None,None,"lo-res")
    )


    return fdict



iconfig = _instrument_configs({})



####################################################################################################

@pytest.mark.skipif(not astropy_status, reason="'astropy' is not available which these test depends on")
@_quash_ethresh_warning
@pytest.mark.parametrize("telescope,instconfig", list(iconfig.items()))
def test_instconfig_pyfits(telescope,instconfig,backend=backend):
    """
    Check that all available instrument configurations are usable using astropy pyfits file I/O backend
    """

    backend = pyfits_backend

    for config in instconfig:
        try:
            rmf,arf = mkdiagresp(telescope,**config._asdict())
        except Warning as exc:
            print(f'{telescope}/{config.instrument} threw a warning: "{exc}"')
            continue

        except (ValueError,RuntimeError) as exc:
            print(f'{telescope}/{config.instrument} threw an error: {exc}')
            continue
        else:
            print(f'{telescope}/{config.instrument}-{config.detector} passed.')



@pytest.mark.skipif(not crates_status, reason="'pycrates' is not available which these test depends on")
@_quash_ethresh_warning
@pytest.mark.parametrize("telescope,instconfig", list(iconfig.items()))
def test_instconfig_crates(telescope,instconfig,backend=backend):
    """
    Check that all available instrument configurations are usable using CIAO's crates file I/O backend
    """

    backend = crates_backend

    for config in instconfig:
        try:
            rmf,arf = mkdiagresp(telescope,**config._asdict())
        except Warning as exc:
            print(f'{telescope}/{config.instrument} threw a warning: "{exc}"')
            continue

        except (ValueError,RuntimeError) as exc:
            print(f'{telescope}/{config.instrument} threw an error: {exc}')
            continue
        else:
            print(f'{telescope}/{config.instrument}-{config.detector} passed.')



backend = crates_backend

####################################################################################################

@_quash_ethresh_warning
@pytest.mark.parametrize("telescope,instconfig", list(iconfig.items()))
def test_instconfig_randomcase(telescope,instconfig,backend=backend):
    """
    Test argument case does not matter
    """
    for config in instconfig:

        randomize_arg_case = config._asdict()

        for key,val in randomize_arg_case.items():
            if isinstance(val,str):
                randomize_arg_case[key] = _randomize_case(val)

        try:
            rmf,arf = mkdiagresp(telescope,**randomize_arg_case)
        except Warning as exc:
            print(f'{telescope}/{config.instrument} threw a warning: "{exc}"')
            continue

        except (ValueError,RuntimeError) as exc:
            print(f'{telescope}/{config.instrument} threw an error: {exc}')
            continue
        else:
            print(f'{telescope}/{config.instrument}-{config.detector} passed.')



####################################################################################################

telescope_config = namedtuple("telescopeconfig", ["telescope","instrument","detector","chantype"])

telescope_args = [ telescope_config("Chandra","ACIS",None,"PHA"),
                   telescope_config("Chandra","ACIS",None,"PI"),
                   telescope_config("XMM","RGS",None,None),
                   telescope_config("Suzaku","XIS",None,None),
                   telescope_config("NuSTAR",None,None,None),
                   telescope_config("eRosita",None,None,None),
                   telescope_config("SRG",None,None,None),
                   telescope_config("NICER",None,None,None),
                   telescope_config("IXPE",None,None,None) ]

telescope_args_fails = [ telescope_config("XMM","EPIC","PN",None),
                         telescope_config("XMM","EPIC","MOS",None) ]

gratings_config = namedtuple("gratingsconfig", ["telescope","instrument","detector","instfilter"])

chandra_gratings_args = [ gratings_config("Chandra","ACIS","HEG",1),
                          gratings_config("Chandra","ACIS","MEG",1),
                          gratings_config("Chandra","ACIS","LEG",1),
                          gratings_config("Chandra","ACIS","HEG",2),
                          gratings_config("Chandra","ACIS","MEG",2),
                          gratings_config("Chandra","ACIS","LEG",2),
                          gratings_config("Chandra","ACIS","HEG",3),
                          gratings_config("Chandra","ACIS","MEG",3),
                          gratings_config("Chandra","ACIS","LEG",3),
                          gratings_config("Chandra","ACIS","HEG",4),
                          gratings_config("Chandra","ACIS","MEG",4),
                          gratings_config("Chandra","ACIS","LEG",4),
                          gratings_config("Chandra","ACIS","HEG",5),
                          gratings_config("Chandra","ACIS","MEG",5),
                          gratings_config("Chandra","ACIS","LEG",5),
                          gratings_config("Chandra","ACIS","HEG",6),
                          gratings_config("Chandra","ACIS","MEG",6),
                          gratings_config("Chandra","ACIS","LEG",6),
                          gratings_config("Chandra","ACIS","HEG",0),
                          gratings_config("Chandra","ACIS","zeroth","0"),
                          gratings_config("Chandra","ACIS","ACIS-7",0),
                          gratings_config("Chandra","ACIS","HEG","-6"),
                          gratings_config("Chandra","ACIS","MEG",-6),
                          gratings_config("Chandra","ACIS","LEG",-6),
                          gratings_config("Chandra","ACIS","HEG",-5),
                          gratings_config("Chandra","ACIS","MEG","-5"),
                          gratings_config("Chandra","ACIS","LEG",-5),
                          gratings_config("Chandra","ACIS","HEG",-4),
                          gratings_config("Chandra","ACIS","MEG","-4"),
                          gratings_config("Chandra","ACIS","LEG",-4),
                          gratings_config("Chandra","ACIS","HEG",-3),
                          gratings_config("Chandra","ACIS","MEG",-3),
                          gratings_config("Chandra","ACIS","LEG","-3"),
                          gratings_config("Chandra","ACIS","HEG",-2),
                          gratings_config("Chandra","ACIS","MEG",-2),
                          gratings_config("Chandra","ACIS","LEG",-2),
                          gratings_config("Chandra","ACIS","HEG",-1),
                          gratings_config("Chandra","ACIS","MEG",-1),
                          gratings_config("Chandra","ACIS","LEG",-1) ]



@pytest.mark.parametrize("args", telescope_args)
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_diagresp(args):
    """
    Test for configuration where a full set of arguments is unnecessary
    """

    msgconfig = _get_configstr(*args)

    print("*" * 80)
    print(f"Running {msgconfig}...", end="\n\n")

    assert mkdiagresp(**args._asdict()), f"{msgconfig} test failed!"



@pytest.mark.xfail
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
@pytest.mark.parametrize("telescope",["erosita","ixpe","nustar"])
def test_broken_lut_path(telescope):
    """
    The tool should error out if the energy grid lookup table files are not found in the
    $ASCDS_INSTALL/data/ebounds-lut directory
    """

    ascds_install = environ["ASCDS_INSTALL"]
    environ["ASCDS_INSTALL"] = _get_random_string(strlen=32)

    try:
        assert mkdiagresp(telescope), "Failed to locate EBOUNDS LUT files..."
    finally:
        environ["ASCDS_INSTALL"] = ascds_install



@pytest.mark.xfail
@pytest.mark.parametrize("args", telescope_args_fails)
def test_diagresp_fails(args):
    """
    Test that arguments provided, which neglects to set a required parameter for the
    instrument configuration, will fail.  If it runs to completion, then the test fails.
    """
    msgconfig = _get_configstr(*args)

    assert not mkdiagresp(**args._asdict()), f"{msgconfig} test should be expected to fail!"



def test_chandra_hrc():
    """
    Test that Chandra/HRC fails correctly
    """
    args = telescope_config("Chandra","HRC",None,None)

    try:

        msgconfig = _get_configstr(*args)

        print("*" * 80)
        print(f"Running {msgconfig}...", end="\n\n")

        mkdiagresp(**args._asdict())

    except RuntimeWarning as exc:
        print(exc)
    finally:
        print(f"~~~~~~~~~~ This test should fail! {msgconfig} should be invalid. ~~~~~~~~~~", end="\n\n")



@pytest.mark.xfail
def test_chandra_hrc2():
    """
    Test that Chandra/HRC fails correctly
    """
    args = telescope_config("Chandra","HRC",None,None)

    assert not mkdiagresp(**args._asdict()), "This test should fail for Chandra/HRC."



@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_channel_offset():
    """
    Test a large channel offset value
    """

    print("*" * 80)
    print("Testing 'EGrid' class and defining an energy grid for generating a non-standard spectral channel offset...", end="\n\n")
    elo,ehi,_ = EGrid("Chandra","ACIS",None,None,None,"PI").get_acis_egrid()

    startchan = 25

    rmf,_ = build_resp(elo, ehi, offset=startchan)

    assert (fchan_min := min(rmf.f_chan)) == startchan, f"Testing with channel offset of {startchan}... minimum 'f_chan' value in the returned RMF object is {fchan_min}.  It is expected that the values should be equal!"



@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_reference_spec_file():
    """
    Test that using a reference (Chandra) spectrum file instead of explicitly
    specifying instrument setup will pick up header keywords and generate responses
    """

    spec = f"{environ['ASCDS_INSTALL']}/test/smoke/data/tools-specextract1.pi"

    rmf,arf = mkdiagresp(refspec=spec)



@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_reference_spec_instance():
    """
    Test that using a reference spectrum PHA object sets up instrument setup
    """

    from sherpa.astro.ui import load_data, get_data

    spec = f"{environ['ASCDS_INSTALL']}/test/smoke/data/tools-specextract1.pi"
    dataid = _get_random_string(strlen=16)
    load_data(dataid,spec)
    specinstance = get_data(dataid)

    rmf,arf = mkdiagresp(refspec=specinstance)



@pytest.mark.xfail
def test_ethresh_none():
    """
    Check that not modifying zero-valued energy bin edges with small-valued 'ethresh'
    is working without throwing an error when set to 'None'
    """

    rmf,arf = mkdiagresp(telescope="nustar", ethresh=None)



@pytest.mark.parametrize("args", chandra_gratings_args)
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_chandra_gratings(args):
    """
    Test for configuration with Chandra gratings arm and diffraction orders
    """

    msgconfig = f"{args.telescope} {args.instrument}/{args.detector}, diffraction order: {args.instfilter}"

    print("*" * 80)
    print(f"Running {msgconfig}...", end="\n\n")

    assert mkdiagresp(**args._asdict()), f"{msgconfig} test failed!"

####################################################################################################

malformed = namedtuple("malformed", ["telescope","instrument","detector","instfilter"])

malformed_config = [ malformed(_shuffle_or_pop_string(tscope),
                               _shuffle_or_pop_string(c.instrument),
                               _shuffle_or_pop_string(c.detector),
                               _shuffle_or_pop_string(c.instfilter))
                     for tscope,configs in iconfig.items()
                     for c in configs ]

good_config = [ malformed(tscope, c.instrument, c.detector, c.instfilter)
                for tscope,configs in iconfig.items()
                for c in configs ]


@pytest.mark.xfail
@_quash_ethresh_warning
@pytest.mark.parametrize("args,orig",
                         list(zip(*[malformed_config, good_config])))
def test_malformed(args,orig):
    """
    use malformed argument values; they should throw errors, albeit some tests
    may pass with valid inputs since the arguments are randomly altered
    """

    if args != orig:
        assert not mkdiagresp(**args._asdict()), "This test is expected to fail!"
    else:
        assert mkdiagresp(**args._asdict()), "This test should have passed!"
