#
#  Copyright (C) 2024
#            Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

"""
Test routines for the diag_resp code
"""

from collections import namedtuple
import pytest

from sherpa.astro.io import backend

try:
    from sherpa.astro.io import crates_backend
    crates_status = True
except (ImportError,ModuleNotFoundError) as exc:
    crates_status = False

try:
    from sherpa.astro.io import pyfits_backend
    astropy_status = True
except (ImportError,ModuleNotFoundError) as exc:
    astropy_status = False

from sherpa_contrib.diag_resp import mkdiagresp, build_resp, EGrid



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

####################################################################################################

@pytest.mark.skipif(not astropy_status, reason="'astropy' is not available which these test depends on")
@pytest.mark.filterwarnings("ignore:.*ENERG_LO value < 0:UserWarning")
@pytest.mark.filterwarnings("ignore:.*ENERG_HI < ENERG_LO:UserWarning")
@pytest.mark.filterwarnings("ignore:.*has a non-monotonic.*array:UserWarning")
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
@pytest.mark.parametrize("telescope,instconfig",
                         [(tscope,config) for tscope,config in _instrument_configs({}).items()])
def test_instconfig_pyfits(telescope,instconfig,backend=backend):
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
@pytest.mark.filterwarnings("ignore:.*ENERG_LO value < 0:UserWarning")
@pytest.mark.filterwarnings("ignore:.*ENERG_HI < ENERG_LO:UserWarning")
@pytest.mark.filterwarnings("ignore:.*has a non-monotonic.*array:UserWarning")
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
@pytest.mark.parametrize("telescope,instconfig",
                         [(tscope,config) for tscope,config in _instrument_configs({}).items()])
def test_instconfig_crates(telescope,instconfig,backend=backend):
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


#backend = crates_backend

####################################################################################################

telescope_config = namedtuple("telescopeconfig", ["telescope","instrument","detector","chantype"])

telescope_args = [ telescope_config("Chandra","ACIS",None,"PHA"),
                   telescope_config("Chandra","ACIS",None,"PI"),
                   telescope_config("XMM","RGS",None,None),
                   telescope_config("Suzaku","XIS",None,None) ]

telescope_args_fails = [ telescope_config("XMM","EPIC","PN",None),
                         telescope_config("XMM","EPIC","MOS",None) ]



@pytest.mark.parametrize("args", telescope_args)
@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_diagresp(args):

    msgconfig = _get_configstr(*args)

    print("*" * 80)
    print(f"Running {msgconfig}...", end="\n\n")

    assert mkdiagresp(**args._asdict()), f"{msgconfig} test failed!"



@pytest.mark.xfail
@pytest.mark.parametrize("args", telescope_args_fails)
def test_diagresp_fails(args):

    msgconfig = _get_configstr(*args)

    assert not mkdiagresp(**args._asdict()), f"{msgconfig} test should be expected to fail!"



def test_chandra_hrc():
    '''
    Test that Chandra/HRC fails correctly
    '''
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



@pytest.mark.filterwarnings("ignore:.*was 0 and has been replaced by*:UserWarning")
def test_channel_offset():
    '''
    test a large channel offset value
    '''

    print("*" * 80)
    print("Testing 'EGrid' class and defining an energy grid for generating a non-standard spectral channel offset...", end="\n\n")
    elo,ehi,_ = EGrid("Chandra","ACIS",None,None,None,"PI").get_acis_egrid()

    startchan = 25

    rmf,_ = build_resp(elo, ehi, offset=startchan)

    assert (fchan_min := min(rmf.f_chan)) == startchan, f"Testing with channel offset of {startchan}... minimum 'f_chan' value in the returned RMF object is {fchan_min}.  It is expected that the values should be equal!"
