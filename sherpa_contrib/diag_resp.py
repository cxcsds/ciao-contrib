#
#  Copyright (C) 2024
#           Smithsonian Astrophysical Observatory
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




""" Create diagonal RMF and flat ARF objects of value unity.

Helper routines for creating a diagonal RMF and flat ARF response
objects for various telescopes and instruments.
The default is to generate Chandra/ACIS responses for PI-type spectra
extracted from ACIS stowed background event files.

Examples
--------

>>> from sherpa_contrib.diag_resp import *
>>> diagrmf,flatarf = mkdiagresp()
>>>
>>> set_rmf(diagrmf, bkg_id=1)
>>> set_arf(flatarf, bkg_id=1)

or

>>> diagrmf,flatarf = mkdiagresp(refspec="bkg.pi")

or

>>> bkgspec = get_bkg()
>>> diagrmf,flatarf = mkdiagresp(refspec=bkgspec)

"""

__revision__ = "18 October 2024"

import os
import warnings
from logging import getLogger
from functools import wraps
from re import sub
from typing import Optional,Union

import numpy.typing as npt
from numpy import arange

from ciao_contrib._tools.fileio import get_keys_from_file

from sherpa.astro.data import DataPHA
from sherpa.astro.ui import create_rmf as shpmkrmf
from sherpa.astro.ui import create_arf as shpmkarf
from sherpa import __version__ as shpver



def _reformat_wmsg(func):
    """
    Decorator:

    Trim extraneous user-warning information showing path and line number
    where Sherpa warning message is being thrown for replacing 0s with ethresh.
    """

    @wraps(func)
    def run_func(*args, **kwargs):
        warnings_reset = warnings.formatwarning
        warnings.formatwarning = lambda msg, *args_warn, **kwargs_warn: f'Warning: {msg}\n'

        func_out = func(*args,**kwargs)

        warnings.formatwarning = warnings_reset

        return func_out

    return run_func



def _arg_case(arg: Optional[Union[str,int,None]]=None,
              lower: bool=False) -> Optional[Union[str,None]]:
    if not isinstance(arg,str):
        return arg

    if lower:
        return arg.lower()

    return arg.upper()



def _get_file_header(fn) -> dict:
    from sherpa.astro.ui import unpack_pha
    from sherpa.utils.logging import SherpaVerbosity

    with SherpaVerbosity("ERROR"):
        return unpack_pha(fn).header



class EGrid:
    """
    gather together all information for non-Chandra setups and return the energy-grid.
    """

    def __init__(self, telescope, instrument, detector, instfilter, nchan, chantype):
        self.telescope = _arg_case(telescope,lower=True)
        self.instrument = _arg_case(instrument,lower=False)
        self.detnam = _arg_case(detector,lower=False)
        self.instfilter = _arg_case(instfilter,lower=False)

        self.subchan = nchan
        self.chantype = chantype

        if self.telescope == "chandra" and self.instrument == "ACIS" and self.detnam is None:
            self.elo,self.ehi,self.offset = self.get_acis_egrid(chantype = self.chantype)
        else:
            self.elo,self.ehi,self.offset = self.get_egrid(telescope = telescope,
                                                           instrument = instrument,
                                                           detnam = detector,
                                                           instfilter = instfilter,
                                                           subchan = nchan,
                                                           chantype = chantype)


    def _set_chantype_none(self, telescope: str = "",
                           instrument: Optional[Union[str,None]] = None,
                           chantype: Optional[Union[str,None]] = None):

        if any([ telescope == "asca" and instrument != "GIS",
                 telescope == "swift" and instrument == "XRT",
                 telescope == "xmm" and instrument == "EPIC",
                 telescope == "xrism" and instrument == "RESOLVE",
                 telescope == "calet",
                 telescope == "chandra" and instrument == "ACIS" and self.detnam is None ]):
            return chantype

        return None


    def _get_ebounds_blk(self, instrument: Optional[Union[str,None]] = None,
                         detnam: Optional[Union[str,None]] = None,
                         instfilter: Optional[Union[str,None]] = None,
                         subchan: Optional[Union[int,None]] = None,
                         chantype: Optional[Union[str,None]] = None) -> str:

        detstr = f"{detnam:->{len(detnam)+1}}" if detnam is not None else ""
        filtstr = f"{instfilter:/>{len(str(instfilter))+1}}" if instfilter is not None else ""
        nchanstr = f"{subchan:_>{len(str(subchan))+1}}chan" if subchan is not None else ""
        chantypestr = f"_{chantype}" if chantype is not None else ""

        blkname = f"{instrument}{detstr}{filtstr}{nchanstr}{chantypestr}"

        return blkname


    def get_acis_egrid(self, chantype: str = "PI") -> tuple[npt.NDArray, npt.NDArray, int]:
        """
        return energy grid and channel offset for Chandra/ACIS detector
        """

        offset: int = 1

        chan = chantype.upper()

        if chan not in ["PI","PHA","PHA_NO-CTICORR"]:
            logger = getLogger(__name__)
            logger.warning("Warning: An invalid 'chantype' provided!  Assuming ACIS PI spectral channel type...")

        if chan.startswith("PHA"):
            detchans: int = 4096

            if chan == "PHA":
                ebin: float = 4.460 # eV CTI corrected
            else:
                ebin: float = 4.485 # eV non-CTI corrected
        else:
            detchans: int = 1024
            ebin: float = 14.6 # eV

        emin = arange(detchans) * (ebinkeV := ebin/1000) # in keV
        emax = emin + ebinkeV # in keV

        return emin, emax, offset


    def get_egrid(self, telescope: str = "",
                  instrument: Optional[Union[str,None]] = None,
                  detnam: Optional[Union[str,None]] = None,
                  instfilter: Optional[Union[str,None]] = None,
                  subchan: Optional[Union[int,None]] = None,
                  chantype: Optional[Union[str,None]] = None) -> tuple[npt.NDArray, npt.NDArray, int]:
        """
        return energy grid and channel offset for a given telescope
        and instrument configuration
        """

        from sherpa.astro.io import read_table_blocks as shp_readtabblk

        fn = f"{os.environ['ASCDS_INSTALL']}/data/ebounds-lut/{self.telescope}-ebounds-lut.fits"

        chantype = self._set_chantype_none(telescope = self.telescope,
                                           instrument = self.instrument,
                                           chantype = self.chantype)

        blkname = self._get_ebounds_blk(instrument = instrument,
                                        detnam = detnam,
                                        instfilter = instfilter,
                                        subchan = subchan,
                                        chantype = chantype)

        try:
            _,blks,hdrs = shp_readtabblk(fn)
            data = None

            for idx,hdr in hdrs.items():
                blk = blk.lower() if (blk := hdr.get("BLKNAME")) is not None else blk

                if blk == blkname.lower():
                    data = blks[idx]
                    break

            if data is None:
                raise IOError(f"Unable to find the '{blkname}' HDU block in {fn}.")

            chan = data["CHANNEL"]
            emin = data["E_MIN"]
            emax = data["E_MAX"]

        except FileNotFoundError:
            raise ValueError("The specified 'telescope' parameter value is invalid; no corresponding lookup table is available.")


        offset = min(chan)

        del shp_readtabblk
        del data

        egrid_unit = get_keys_from_file(f"{fn}[{blkname}]")["EUNIT"]

        if egrid_unit == "eV":
            ## convert eV to keV ##
            emin /=  1_000
            emax /=  1_000

        if egrid_unit == "MeV":
            ## convert MeV to keV ##
            emin *= 1_000
            emax *= 1_000

        if egrid_unit == "GeV":
            ## convert MeV to keV ##
            emin *= 1_000_000
            emax *= 1_000_000

        return emin, emax, offset



class Check_and_Update_Info:
    """
    revise telescope/instrument configuration information to the
    minimal parameters required to obtain the necessary energy grid
    """

    def __init__(self, telescope, instrument, detnam, instfilter, chantype):

        ### update telescopes with alternate names and validate parameter setting ###
        telescope = self.check_tscope(telescope)


        chantype = self.check_chantype(telescope,instrument,detnam,chantype)


        ### check 'instrument' and 'detector' arguments ###
        instrument, detnam = self.check_inst_det(telescope,instrument,detnam)


        ### check 'instfilter' argument ###
        instfilter, detnam = self.set_instfilter(telescope,instrument,detnam,instfilter)


        self.telescope = telescope
        self.instrument = instrument
        self.detector = detnam
        self.instfilter = instfilter
        self.chantype = chantype


    def _varcheck(self, var: str = "", varcheck: list[str] = None,
                  tscopestr: str = "", parname: str = "instrument",
                  inststr:  Optional[Union[None,str]] = None, stripnum: bool = False):
        """
        raise ValueError if parameter is not appropriately set with valid value
        """
        if var is None or var not in varcheck:
            if stripnum:
                varcheck = set(sub(r"\d+", "", v) for v in varcheck)


            estr = '|'.join([f"'{v}'" for v in varcheck])

            if inststr is not None:
                raise ValueError(f"'telescope={tscopestr}' with 'instrument={inststr}' requires the '{parname}' argument to be: {estr}")

            raise ValueError(f"'telescope={tscopestr}' requires '{parname}' argument to be: {estr}")


    def check_tscope(self, telescope: str=""):
        """
        check telescope parameter and update with alternate names if needed
        """

        if telescope == "" or telescope is None:
            raise ValueError("'telescope' parameter must be specified!")


        ### update telescopes with alternate names ###
        alt_tscope_name = { "xte" : "rxte",
                            "sax" : "bepposax",
                            "erosita" : "srg" }

        if telescope in alt_tscope_name:
            telescope = alt_tscope_name.get(telescope)


        ### check telescopes are supported ###
        valid_tscopes = { "asca" : "ASCA",
                          "bepposax" : "BeppoSAX",
                          "calet" : "CALET",
                          "chandra" : "Chandra",
                          "cos-b" : "COS-B",
                          "einstein" : "Einstein",
                          "exosat" : "EXOSAT",
                          "halosat" : "HALOSAT",
                          "ixpe" : "IXPE",
                          "maxi" : "MAXI",
                          "nicer" : "NICER",
                          "nustar" : "NuSTAR",
                          "rosat" : "ROSAT",
                          "rxte" : "RXTE",
                          "srg" : "SRG",
                          "suzaku" : "Suzaku",
                          "swift" : "Swift",
                          "xmm" : "XMM",
                          "xrism" : "XRISM" }

        if telescope not in valid_tscopes:
            estr = '|'.join([f"'{v}'" for v in valid_tscopes.values()])
            raise ValueError(f"The provided 'telescope' value is not supported. Valid string values are: {estr}")


        return telescope


    def set_instfilter(self, telescope: str = "",
                       instrument: Optional[Union[str,None]] = None,
                       detnam: Optional[Union[str,None]] = None,
                       instfilter: Optional[Union[str,int,None]] = None):
        """
        setup 'instfilter' argument; only Swift/UVOT and Chandra/gratings
        energy-grids are dependent on this quantity
        """

        if telescope == "swift" and instrument == "UVOT":
            self._varcheck(detnam, ["B","V","U","UVM2","UVW1","UVW2","WHITE"],
                           tscopestr="Swift", inststr="UVOT", parname="instfilter")

        elif telescope == "chandra" and instrument == "ACIS" and detnam is not None:
            if instfilter is not None and int(instfilter) == 0:
                instfilter = None
                detnam = None

            if detnam not in ["HEG","MEG","LEG",None]:
                raise ValueError("ACIS gratings arm is set with 'detector' argument 'HEG'|'MEG'|'LEG'")

            if detnam is not None and instfilter is not None:
                emsg = "ACIS gratings arm diffraction order is defined by 'instfilter' parameter with integer values: 1|2|3|4|5|6|-6|-5|-4|-3|-2|-1"

                if isinstance(instfilter,str) and not instfilter.lstrip("-").isdigit():
                    raise ValueError(emsg)

                instfilter = abs(int(instfilter))

                if instfilter not in range(1,7):
                    raise ValueError(emsg)

        else:
            instfilter = None


        return instfilter, detnam


    def check_inst_det(self, telescope: str = "",
                       instrument: Optional[Union[str,None]] = None,
                       detnam: Optional[Union[str,None]] = None):

        """
        check validity of "instrument" and "detector" arguments and set to None when the arguments will go unused
        """

        ### set detector value to None for telescopes with only a single instrument ###
        if telescope in ("nustar","einstein","cos-b",
                         "exosat","halosat","ixpe",
                         "maxi","nicer","rosat","srg"):
            detnam = None

        if telescope == "chandra" and instrument == "ACIS" and detnam is not None and detnam.startswith(instrument):
            detnam = None


        ### update telescopes with unique energy grid, even if there are multiple instruments ###
        unique_inst_egrid = { "cos-b" : "COS-B",
                              "exosat" : "CMA",
                              "halosat" : "SDD",
                              "ixpe" : "GPD",
                              "maxi" : "GSC",
                              "nicer" : "XTI",
                              "rosat" : "PSPC",
                              "srg" : "eROSITA",
                              "nustar" : "FPM" }

        if telescope in unique_inst_egrid:
            instrument = unique_inst_egrid.get(telescope)


        ### check all other instrument and detector setups ###
        checks = { "chandra" : self._check_chandra,
                   "einstein" : self._check_einstein,
                   "asca" : self._check_asca,
                   "bepposax" : self._check_bepposax,
                   "calet" : self._check_calet,
                   "rxte" : self._check_rxte,
                   "suzaku" : self._check_suzaku,
                   "swift" : self._check_swift,
                   "xmm" : self._check_xmm,
                   "xrism" : self._check_xrism }


        runchecks = checks.get(telescope)

        if runchecks is not None:
            instrument,detnam = runchecks(instrument,detnam)

        return instrument, detnam


    def _check_chandra(self,inst,det):

        ### check for Chandra/HRC, which *may be* suitable for crude hardness ratio estimates ###
        if inst == "HRC":
            raise RuntimeWarning("non-grating HRC data has insufficient spectral resolution to be suitable for spectral fitting!")

        self._varcheck(inst, ["ACIS"], tscopestr="Chandra")

        return inst,det


    def _check_einstein(self,inst,det):
        self._varcheck(inst, ["HRI","IPC","SSS","MPC"], tscopestr="Einstein")

        return inst,det


    def _check_asca(self,inst,det):
        self._varcheck(inst, ["GIS","SIS0","SIS1"], tscopestr="ASCA")

        if inst.startswith("SIS"):
            self._varcheck(det, ["CCD0","CCD1","CCD2","CCD3"],
                           tscopestr="ASCA", inststr="SIS0|SIS1", parname="detector")

        else:
            det = None

        return inst,det


    def _check_bepposax(self,inst,det):
        self._varcheck(inst, ["PDS","HPGSPC","LECS","MECS","WFC1","WFC2"], "BeppoSAX|SAX")

        if inst == "MECS":
            self._varcheck(det, ["M1","M2","M3"],
                           tscopestr="BeppoSAX|SAX", inststr="MECS", parname="detector")

        else:
            det = None

        return inst,det


    def _check_calet(self,inst,det):
        inst = "GGBM"

        if det is not None and det.startswith("HXM"):
            det = "HXM"

        self._varcheck(det, ["HXM","SGM"], tscopestr="CALET", parname="detector")

        return inst,det


    def _check_rxte(self,inst,det):
        self._varcheck(inst, ["HEXTE","PCA"], tscopestr="RXTE|XTE")

        if inst == "HEXTE":
            self._varcheck(det, ["PWA","PWB"],
                           tscopestr="RXTE|XTE", inststr="MECS", parname="detector")

        else:
            det = None

        return inst,det


    def _check_suzaku(self,inst,det):
        self._varcheck(inst, ["HXD","XRS","XIS","XIS0","XIS1","XIS2","XIS3"],
                       tscopestr="Suzaku", stripnum=True)

        if inst.startswith("XIS"):
            inst = "XIS"

        if inst == "HXD":
            self._varcheck(det, ["WELL_GSO","WELL_PIN"],
                           tscopestr="Suzaku", inststr="HXD", parname="detector")

        else:
            det = None

        return inst,det


    def _check_xmm(self,inst,det):
        if inst is None or inst not in ["RGS","EPIC","EPN","EMOS1","EMOS2"]:
            raise ValueError("'telescope=XMM' requires 'instrument' argument to be EPIC|RGS")

        if inst == "EPIC":
            if det is None or all([det != "PN", not det.startswith("MOS")]):
                raise ValueError("'telescope=XMM' with 'instrument=EPIC' requires the 'detector' argument to be PN|MOS")

            if det.startswith("MOS"):
                det = "MOS"

        if inst == "RGS":
            det = None

        if inst.startswith("EMOS"):
            inst = "EPIC"
            det = "MOS"

        if inst.startswith("EPN"):
            inst = "EPIC"
            det = "PN"

        return inst,det


    def _check_xrism(self,inst,det):
        self._varcheck(inst, ["XTEND","RESOLVE"],
                       tscopestr="XRISM")

        return inst,det


    def _check_swift(self,inst,det):
        if inst not in ["XRT","BAT","UVOTA","UVOT"]:
            raise ValueError("'telescope=Swift' requires 'instrument' argument to be XRT|BAT|UVOT")

        if inst.startswith("UVOT"):
            inst = "UVOT"

        det  = None

        return inst,det


    def check_chantype(self,telescope,instrument,detector,chantype):
        _chantype_lower = _arg_case(chantype,lower=True)

        ### set Chandra/ACIS gratings channel ###
        if telescope == "chandra" and instrument == "ACIS" and detector is not None and _chantype_lower != "pi":
            logger_tmp = getLogger(__name__)
            logger_tmp.info("Note: Assuming PI spectral channel type for ACIS gratings data set...")
            chantype = "PI"
            _chantype_lower = "pi"

        if telescope == "chandra" and instrument == "ACIS" and detector is None and _chantype_lower not in ["pi","pha","pha_no-cticorr"]:
            raise ValueError("Chandra/ACIS requires 'chantype' argument to be set to 'PI', 'PHA', or 'PHA_no-CTIcorr'.")

        if telescope == "calet" and _chantype_lower not in ["gain_lo","gain_hi"]:
            raise ValueError("CALET requires 'chantype' argument to be set to 'GAIN_HI' or 'GAIN_LO'.")

        if telescope == "xrism" and instrument == "RESOLVE" and _chantype_lower not in ["lo-res","mid-res","hi-res"]:
            raise ValueError("XRISM RESOLVE requires 'chantype' argument to be set to 'lo-res', 'mid-res', or 'hi-res'.")

        return chantype



@_reformat_wmsg
def build_resp(emin, emax, offset: int, ethresh: Optional[Union[float,None]] = 1e-12):
    """
    Return a diagonal RMF and flat ARF data objects with matching energy grid.
    Use set_rmf and set_arf on the respective instances.

    Parameters:
        emin - array of energy grid lower bin edge
        emax - array of energy grid upper bin edge
        offset - integer-value starting channel number, typically 0 or 1.
        ethresh - number or None, controls whether zero-energy bins are replaced.

    """

    logger = getLogger(__name__)

    try:
        flatarf = shpmkarf(emin, emax, ethresh=ethresh)
        diag_rmf = shpmkrmf(emin, emax, startchan=offset, ethresh=ethresh)

        #################################################################
        ### remove once 'startchan' is factored into channel enumeration
        ### in sherpa/astro/instrument.py, or use a version test on
        ### whether this incrementation should be done

        major,minor,micro = shpver.split(".")
        ver = float(f"{major}.{minor}")
        #ver_micro = int(micro)

        if ver < 4.17 and offset != 1:
            diag_rmf.f_chan += offset - 1

        #################################################################

    except Exception as exc:
        if repr(exc).find("value <= 0") != -1:

            raise RuntimeError(f"{exc.args[0]}.  Set 'ethresh' to a float value greater than zero and not None.") from None

        logger.warning(exc)
        raise RuntimeError(exc) from exc


    wmsg = "RMF and ARF data objects returned; use 'set_rmf' and 'set_arf' to set the respective instances to dataset ID."

    logger.warning("%s", f"\n{wmsg:>{len(wmsg)+4}}")


    return diag_rmf, flatarf



def mkdiagresp(telescope: str = "Chandra",
               instrument: str = "ACIS",
               detector: Optional[Union[str,None]] = None,
               instfilter: Optional[Union[str,int,None]] = None,
               refspec: Optional[Union[str,DataPHA,None]] = None,
               chantype: str = "PI",
               nchan: Optional[Union[int,None]] = None,
               ethresh: Optional[Union[float,None]] = 1e-12):
    """
    Return a diagonal RMF and flat ARF data objects with matching energy grid for a specified instrument/detector.
    Use set_rmf and set_arf on the respective instances.  Use 'build_resp' for a non-instrument specific [or generalized] energy-grid configuration.

    "PI" channel-type is the default, assumed spectral type.


    Supported arguments:

        telescope="Chandra"
            instrument="ACIS"
            chantype="PI"|"PHA"|"PHA_no-CTIcorr"

            instrument="ACIS"
            detector="HEG"|"MEG"|"LEG" # HETG or LETG grating arm
            instfilter=1|2|3|4|5|6|-6|-5|-4|-3|-2|-1 # grating diffraction order
            chantype="PI"

        telescope="ASCA"
            instrument="GIS"
                nchan=[ 1024 | 256 | 128 ]

            instrument="SIS0"|"SIS1"
                detector="CCD0"|"CCD1"|"CCD2"|"CCD3"
                chantype="PI"|"PHA"
                nchan=[ 1024 | 512 ]

        telescope="BeppoSAX"|"SAX"
            instrument="WFC1"|"WFC2"|"HPGSPC"|"LECS"

            instrument="PDS"
                nchan=[ 256 | 128 | 60 ]

            instrument="MECS"
                detector="M1"|"M2"|"M3"

        telescope="CALET"
            instrument="GGBM"
                detector="SGM"|"HXM"
                chantype="GAIN_HI"|"GAIN_LO"

        telescope="COS-B"
            instrument="COS-B"

        telescope="Einstein"
            instrument="HRI"|"IPC"|"SSS"|"MPC"

        telescope="EXOSAT"
            instrument="CMA"

        telescope="HALOSAT"
            instrument="SDD"

        telescope="IXPE"
            instrument="GPD"

        telescope="MAXI"
            instrument="GSC"

        telescope="NICER"
            instrument="XTI"

        telescope="NuSTAR"
            instrument="FPM"

        telescope="ROSAT"
            instrument="PSPC"
            nchan=[ 256 | 34 ]

        telescope="RXTE"|"XTE"
            instrument="PCA"
                nchan=[ 256 | 6 ]

            instrument="HEXTE"
                detector="PWA"|"PWB"

        telescope="SRG"|"eROSITA"
            instrument="eROSITA"

        telescope="Suzaku"
            instrument="XIS"|"XRS"

            instrument="HXD"
                detector="WELL_GSO"|"WELL_PIN"

        telescope="Swift"
            instrument="BAT"

            instrument="XRT"
                chantype="PI"|"PHA"

            instrument="UVOT"
                instfilter="B"|"V"|"U"|"UVM2"|"UVW1"|"UVW2"|"WHITE"

        telescope="XMM"
            instrument="RGS"

            instrument="EPIC"
                detector="MOS"|"PN"
                chantype="PI"|"PHA"

        telescope="XRISM"
            instrument="XTEND"

            instrument="RESOLVE"
                chantype="lo-res"|"mid-res"|"hi-res"

    """

    if refspec is not None:
        if isinstance(refspec,str):
            # speckw = _get_file_header(refspec)
            speckw = get_keys_from_file(refspec)

        if isinstance(refspec,DataPHA):
            speckw = refspec.header

        for k,v in speckw.items():
            if isinstance(v,str) and v.lower() in ['none','']:
                speckw[k] = None

        telescope = speckw.get("TELESCOP")
        instrument = speckw.get("INSTRUME")
        detector = speckw.get("DETNAM")
        instfilter = speckw.get("FILTER")
        nchan = speckw.get("DETCHANS")
        chantype = speckw.get("CHANTYPE")

        grating = speckw.get("GRATING")

        if telescope.lower() == "chandra" and grating not in [None,"NONE","None","none"]:
            chandra_TG_PART = { 1 : "HEG",
                                2 : "MEG",
                                3 : "LEG",
                                0 : "zeroth" }

            tg_m = speckw.get("TG_M")
            tg_part = speckw.get("TG_PART")

            if tg_m in chandra_TG_PART and tg_part is not None:
                detector = chandra_TG_PART[tg_part] if tg_part != 0 else None
                instfilter = tg_m if tg_m != 0 else None

            if (tg_m is None and tg_part is None) or grating.lower() == "none":
                detector = None
                instfilter = None


    telescope = _arg_case(telescope,lower=True)
    instrument = _arg_case(instrument)
    detector = _arg_case(detector)
    instfilter = _arg_case(instfilter)


    ### run arguments check and update parameters to minimal information needed ###
    update_args = Check_and_Update_Info(telescope=telescope, instrument=instrument,
                                        detnam=detector, instfilter=instfilter, chantype=chantype)

    telescope = update_args.telescope
    instrument = update_args.instrument
    detector = update_args.detector
    instfilter = update_args.instfilter
    chantype = update_args.chantype


    ### instruments/detectors with more than one channel binning scheme ###
    multichan_resps_max = { "asca sis" : 1024,
                            "asca gis" : 1024,
                            "rosat pspc" : 256,
                            "rxte pca" : 256,
                            "bepposax pds" : 256 }

    key = f"{telescope} {''.join(i for i in instrument if not i.isdigit())}".lower()

    if any([
            (chantest := multichan_resps_max.get(key)) is not None and chantest == nchan,
            key not in multichan_resps_max
    ]):
        nchan = None


    ### return energy grid and first enumerated spectral channel ###
    egrid = EGrid(telescope, instrument, detector,
                  instfilter, nchan, chantype)

    elo = egrid.elo
    ehi = egrid.ehi
    offset = egrid.offset


    # for Einstein/SSS, the first three energy bins are zeros;
    # tweak the values to avoid '<= the replacement value of'
    # RuntimeError being thrown right off the bat
    if telescope == "einstein" and instrument == "SSS":
        elo[1] = 1e-12 + 1e-16
        elo[2] = elo[1] + 1e-16
        ehi[0] = elo[1]
        ehi[1] = elo[2]


    return build_resp(emin=elo, emax=ehi, offset=offset, ethresh=ethresh)
