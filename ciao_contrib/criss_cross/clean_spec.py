# Copyright (C) 2022,2025 MIT
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
clean_spec - Uses confusion tables produced by CrissCross to create 'cleaned' PHA1 or PHA2 spectra and ARF response files.
"""

from load_hetg_resp import find_resp_files, match_resp_order
#from from sherpa_contrib.load_hetg_resp import find_resp_files, match_resp_order
import numpy as np
from constants import tg_part_name
import ciao_contrib.logger_wrapper as lw

from pycrates import (
    read_file,
    write_file,
    get_keyval,
    read_pha,
    write_pha,
    is_pha_type1,
    is_pha_type2,
    update_crate_checksum,
)

TOOLNAME = 'clean_spec'
__revision__  = '28 May 2026'

lw.initialize_logger(TOOLNAME)
v1 = lw.make_verbose_level(TOOLNAME, 1)
v2 = lw.make_verbose_level(TOOLNAME, 2)
v3 = lw.make_verbose_level(TOOLNAME, 3)

def clean_spec(cc_table, pha_file, spec_root, arf_file=None, resp_dir=None, clobber=False):
    """
    Uses confusion tables produced by CrissCross to create 'cleaned' PHA1 or PHA2 spectra and ARF response files. The
    confusion tables identify portions of a source's spectrum that may have erroneous events that should not be
    included in any spectral analysis. After identifying the PHA type (1 vs 2), this function checks to make sure the
    ARF files provided match the PHA spectra (order and arm) and uses clean_data() to set the appropriate PHA
    (COUNTS, STAT_ERROR) and ARF (SPECRESP, FRACEXPO) columns to zero where confusion occurs. This function writes a
    'cleaned' copy of the input PHA and ARF files.

    Parameters
    ----------

    cc_table: fits table
        CrissCross produced confusion table for a single source and single obsID.
    pha_file: fits file
        HETG PHA1 or PHA2 spectral file of the source that needs cleaning.
    spec_root: string
        A root for file naming purposes.
    arf_file: string or list
        A file path or list of file paths to ARFs matching the input pha file.
    resp_dir: directory
        The directory where the ARFs associated with the pha_file is stored.
    clobber: Bool
        If clobber=True then output file will be over-written.

    """

    def clean_data(
        cc_table,
        pha_crate,
        arf_file_var,
        pha_element,
        conf_flag_var="confused",
    ):
        """
        Creates copies of the relevant PHA1/PHA2 and ARF columns and modifies them (sets to zero) using a CrissCross
        confusion table.

        Parameters
        ----------

        cc_table: fits table
            CrissCross produced confusion table for a single source and single obsID.
        pha_crate: Crate object
            The Crate data for a single spectrum (e.g., HEG+1)
        arf_file_var: string
            A file path to an ARF matching the input pha file.
        pha_element: integer
            The element of the PHA2 file assocaited with the spectrum 'pha_crate'. If standard HETG PHA2 file
            [order,element] = HEG: -3,0; -2,1; -1,2; +1,3; +2,4; +3,5 MEG: -3,6; -2,7; -1,8; +1,9; +2,10; +3,11)
        conf_flag_var: string 'confused'
            The string associated with spectral confusion. If 'confused', spectra will be cleaned by setting all
            'confused' values to zero. A future update will allow 'confused' and/or 'warn' to be zeroed out.


        Returns
        ----------

        cleaned_spec_var, cleaned_staterr_var, cleaned_specresp_var, cleaned_fracexpo_var: arrays
            Returns a copy of the SPEC, STAT_ERR, SPECRESP, and FRACEXPO arrays with values associated with the
            identified wavelengths of confusion set to zero (or 1.86603 for STAT_ERR).
        """

        # reads in the confusion and PHA data
        cc_data = read_file(cc_table)
        pha_data_var = pha_crate.get_crate(2)
        arf_data_var = read_file(arf_file_var)

        # identifies ARF tg_m, tg_order, and tg_part 
        arf_tg_part = get_keyval(arf_data, "TG_PART")
        arf_tg_m = get_keyval(arf_data, "TG_M")

        # PHA1 and PHA2 files have to be treated slightly differently because of how crates stores values. This is to
        # avoid having to slice off each crate spectrum from the PHA2 file.
        if is_pha_type1(pha_crate):
            counts_arr = pha_data_var.COUNTS.values
            stat_err_arr = pha_data_var.STAT_ERR.values
            specresp_arr = arf_data_var.SPECRESP.values
            fracexpo_arr = arf_data_var.FRACEXPO.values
            bin_low_arr = pha_data_var.BIN_LO.values
            bin_high_arr = pha_data_var.BIN_HI.values

        elif is_pha_type2(pha_crate):
            counts_arr = pha_data_var.COUNTS.values[pha_element]
            stat_err_arr = pha_data_var.STAT_ERR.values[pha_element]
            specresp_arr = (
                arf_data_var.SPECRESP.values
            )  # ARFs are not in PHA2 (array) format and thus don't need a pha_element
            fracexpo_arr = (
                arf_data_var.FRACEXPO.values
            )  # ARFs are not in PHA2 (array) format and thus don't need a pha_element
            bin_low_arr = pha_data_var.BIN_LO.values[pha_element]
            bin_high_arr = pha_data_var.BIN_HI.values[pha_element]

        else:
            raise ValueError("PHA datatype must be 1 or 2")

        # copies the counts and stat_err column of the PHA file for modification
        cleaned_spec_var = counts_arr.copy()
        cleaned_staterr_var = stat_err_arr.copy()

        # copies the SPECRESP and fracexpo columns from the arf
        cleaned_specresp_var = specresp_arr.copy()
        cleaned_fracexpo_var = fracexpo_arr.copy()

        # for every row of the confusion table that match the input PHA spectrum order and tg_part, identify the
        # elements (rows) associated with wavelengths (bin_low and bin_hi) that need to be cleaned. Note, this assumes
        # the PHA bin_lo and bin_hi values are identical to the ARF file (which should be the case).
        for i in range(0, len(cc_data.wave_low.values)):
            if (
                cc_data.flag.values[i] == conf_flag_var
                and cc_data.grating_type.values[i] == tg_part_name[arf_tg_part]
                and cc_data.order.values[i] == arf_tg_m
            ):
                elements_to_clean = np.where(
                    (bin_low_arr >= cc_data.wave_low.values[i])
                    & (bin_high_arr <= cc_data.wave_high.values[i])
                )  # identify elements

                # clean PHA (spectrum)
                cleaned_spec_var[elements_to_clean] = (
                    0.0  # set elements that overlap to zero
                )
                cleaned_staterr_var[elements_to_clean] = (
                    1.86603  # double check that this makes sense and the stat_err is always this value for zero counts.
                    # I suspect instead I should take min of this column and set it to that.
                )

                # clean ARF (response)
                cleaned_specresp_var[elements_to_clean] = 0.0
                cleaned_fracexpo_var[elements_to_clean] = 0.0

        # return the cleaned arrays values.
        return (
            cleaned_spec_var,
            cleaned_staterr_var,
            cleaned_specresp_var,
            cleaned_fracexpo_var,
        )

    # Read the PHA file and determine if PHA1 or PHA2. Uses read_pha() to bring along the necessary PHA extensions.
    pha_crate_dataset = read_pha(pha_file)

    if is_pha_type1(pha_crate_dataset):
        pha_data = pha_crate_dataset.get_crate(2)  # Crate 2 contains the PHA data
        arf_data = read_file(arf_file)

        # determine the heg/meg arm, order and obsID of the PHA spectrum and make sure it matches the ARF
        tg_part = get_keyval(
            pha_data, "TG_PART"
        )  # tg_part = 1 = heg; tg_part = 2 = meg
        tg_m = get_keyval(pha_data, "TG_M")
        tg_obs = get_keyval(pha_data, "OBS_ID")
        tg_part_arf = get_keyval(arf_data, "TG_PART")
        tg_m_arf = get_keyval(arf_data, "TG_M")
        tg_obs_arf = get_keyval(arf_data, "OBS_ID")

        # if parameters dont match between ARF and PHA then throw error
        if tg_obs != tg_obs_arf or tg_m != tg_m_arf or tg_part != tg_part_arf:
            raise ValueError(
                "One of the following is not consistent between the PHA file and ARF: HEG/MEG arm, order, obsID"
            )

        # use clean_data() to create copies of the appropriate PHA and ARF arrays where wavelenghts with confusion are
        # set to 0
        cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(
            cc_table=cc_table,
            pha_crate=pha_crate_dataset,
            arf_file_var=arf_file,
            pha_element=0,
            conf_flag_var="confused",
        )

        # replaces the original arrays in the loaded crates with the new arrays
        pha_data.COUNTS.values = cleaned_spec
        pha_data.STAT_ERR.values = cleaned_staterr
        arf_data.SPECRESP.values = cleaned_specresp
        arf_data.FRACEXPO.values = cleaned_fracexpo

        # appends the original files to the history for record keeping
        pha_data.add_record(
            "HISTORY",
            f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ",
        )
        arf_data.add_record(
            "HISTORY",
            f"This cleaned ARF was created using the ARF file: {arf_file} and the CrissCross cleaning table: {cc_table}. ",
        )

        update_crate_checksum(pha_data)
        update_crate_checksum(arf_data)

        # setup tgpart and order to be consistent with values in confusion tables for file naming.
        pha_arm = tg_part_name[tg_part]
        pha_order = f"{tg_m:+n}"

        # saves a new file while maintaining the original header.
        write_pha(
            pha_crate_dataset,
            f"{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.pha",
            clobber=clobber,
        )
        write_file(
            arf_data,
            f"{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.arf",
            clobber=clobber,
        )

    # PHA2 files need to be treated a little different because they are arrays of arrays and order/arm info is not in
    # header. Also the arfs may be out of order if user provides a list of arfs.
    elif is_pha_type2(pha_crate_dataset):
        # if user enters their own arf or list of arfs then make sure they match the PHA2 file format (e.g., pha2 meg+1
        # has to be same array element as arf meg+1)
        if arf_file is not None:
            if type(arf_file) is str:
                arf_file = list(
                    [arf_file]
                )  # make sure arf_file variable is a list just in case user enters a single file as 'file1' instead of ['file1'].

            # check and arrange that the user input arf file(s) are in the correct order of the PHA2 spectra.
            # matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(
                pha2_file=pha_file, resp_list=arf_file, resp_type="arf"
            )

        # if user doesn't enter arfs then try to find them either using the user included response dir or the standard
        # CIAO-produced file structure
        else:
            v1(
                "Warning, no ARF response files provided in parameter arf_file. Attempting to find them."
            )
            resp_list = find_resp_files(
                pha2_file=pha_file, resp_type="arf", resp_dir=resp_dir
            )

            if len(resp_list) == 0:
                raise ValueError(
                    "No response files found. Try including a directory with resp_dir or include a list of response paths with arf_file parameter."
                )

            # matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(
                pha2_file=pha_file, resp_list=resp_list, resp_type="arf"
            )

        # read the PHA data and obtain the tg_m, tg_part and obsID values
        pha_data_full = pha_crate_dataset.get_crate(2)

        tg_m_arr = pha_data_full.TG_M.values
        tg_part_arr = pha_data_full.TG_PART.values
        tg_obs = get_keyval(pha_data_full, "OBS_ID")

        pha_order_arr = [
            f"{i:+n}" for i in tg_m_arr
        ]  # this is to make sure the order has a + or - sign in front of it for file naming purposes
        pha_arm_arr = [
            tg_part_name[i] for i in tg_part_arr
        ]  # this is to make sure the arm is named 'heg' or 'meg' for file naming purposes

        # only run clean_data() for the spectra that have a matched response file so identify which elements of the
        # matched_resp_list have both a spectrum and associated ARF.
        spec_to_clean = np.where(
            matched_resp_list != "no match"
        )[
            0
        ]  # note, the 'no match' string comes from match_resp_order() so be careful if that changes.

        # run clean_data() for every arm and order which have a spectrum and matching ARF
        for i in spec_to_clean:
            arf_data = read_file(
                matched_resp_list[i]
            )  # load the arf from match_resp_list because it is already matched to the appropriate PHA2 file

            cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = (
                clean_data(
                    cc_table=cc_table,
                    pha_crate=pha_crate_dataset,
                    arf_file_var=matched_resp_list[i],
                    pha_element=i,
                    conf_flag_var="confused",
                )
            )

            # replaces the original arrays with the new arrays
            pha_data_full.COUNTS.values[i] = cleaned_spec
            pha_data_full.STAT_ERR.values[i] = cleaned_staterr
            arf_data.SPECRESP.values = cleaned_specresp
            arf_data.FRACEXPO.values = cleaned_fracexpo

            # update the ARF header and write out the file
            arf_data.add_record(
                "HISTORY",
                f"This cleaned ARF was created using the ARF file: {matched_resp_list[i]} and the CrissCross cleaning table: {cc_table}. ",
            )
            update_crate_checksum(arf_data)

            write_file(
                arf_data,
                f"{spec_root}_obsid_{tg_obs}_{pha_arm_arr[i]}{pha_order_arr[i]}_cleaned.arf",
                clobber=clobber,
            )

        # appends the original files to the history of the new file for record keeping
        pha_data_full.add_record(
            "HISTORY",
            f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ",
        )

        update_crate_checksum(pha_data_full)

        # saves a new PHA2 file while maintaining the original header.
        write_pha(
            pha_crate_dataset, f"{spec_root}_obsid_{tg_obs}_cleaned.pha2", clobber=clobber
        )
    else:
        raise ValueError("Input PHA file was not a PHA1 or PHA2 type file")

    return ()
