
import numpy as np
import glob
from pycrates import (
    read_file,
    get_keyval,
    read_pha,
    get_history_records,
)

from pathlib import Path

def find_resp_files(pha2_file_par, resp_type_par, resp_dir_par=None):
    """
    Identifies ARFs and RMFs that are associated with an HETG PHA2 file.  This currently utilizes the 'response' and
    'tg' directories created by the data systems and chandra_repro pipelines and thus might not work for all PHA2 HETG
    files.

    Parameters
    ----------

    pha2_file_par : PHA2 fits file
         PHA2 spectrum which is typically provided in the chandra archive of a downloaded HETG observation or after
         running chandra_repro on a chandra HETG obsID.
    resp_type_par: 'arf' or 'rmf'
        The type of response files for matchign to PHA spectra
    resp_dir_par: directory
        The directory where the HETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.

    Returns
    ----------
    resp_list_par: list
    Returns a list of ARF or RMF files found.

    """

    # if user enters 'ARF' or 'RMF' then lower case for later glob use
    resp_type_par = resp_type_par.lower()

    # check to make sure responses are either arf or rmf
    if resp_type_par != "arf" and resp_type_par != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # load the pha2 file and obtain the crate where relevant information is stored
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)

    # identify the number of spectra in the PHA2 file
    num_spec_par = len(spec_crate_par.TG_M.values)

    # determine which pipeline the PHA2 file came from (archive vs CIAO user)
    creator_key = get_keyval(spec_crate_par, "CREATOR")

    if "Version DS" in creator_key:

        # if users pha2_file_par is a long path or a single file, strip the name and check for the root so the resp 
        # glob doesn't get any extra unrelated files in the response dir.

        # Note, the strings in this section are based on the DS standard naming.
        pha_name = Path(pha2_file_par).name
        pha_root = pha_name.partition("_pha2.fits")[0]

        if resp_dir_par != None:  # use provided resp_dir_par
            resp_list_par = glob.glob(
                f"{resp_dir_par}/{pha_root}*{resp_type_par}2.fits*"
            )
        else:
            pha_dir = Path(
                pha2_file_par
            ).parent  # need to get directory where PHA2 file is located
            resp_list_par = glob.glob(
                f"{pha_dir}/responses/{pha_root}*{resp_type_par}2.fits*"
            )

    elif (
        "Version CIAO" in creator_key
    ):  # this is produced via chandra_repro or user custom spectral extraction

        # read the header to search for the PHA2 root name which is often the same root as the responses
        hist = get_history_records(spec_crate_par)
        pha_root = ""  # set to '' for checking later in case pha_root not found

        # if chandra_repro was used to produce the PHA2 file then a ':root" value is saved in the header history. 
        # This identifies that value.
        for i in range(0, len(hist)):
            if ":root=" in hist[i][1]:  # find the line where the :root command was used
                root_line = (
                    hist[i][1].split("=", 1)[1].strip()
                )  # strip the unnecessary stuff but leaves the extra spaces
                pha_root = root_line.split(" ")[
                    0
                ]  # remove everything after the root value
                break  # stops searching hist for the appropriate line after it is found

        # if pha_root is not overwritten at this point then throw error because it means it was not found
        if pha_root == "":
            raise ValueError(
                "Could not identify PHA2 file root. Please load responses manually."
            )

        # use glob and pha_root to find the responses
        if resp_dir_par != None:  # use provided resp_dir_par
            resp_list_par = glob.glob(f"{resp_dir_par}/{pha_root}*.{resp_type_par}")
        else:
            pha_dir = Path(
                pha2_file_par
            ).parent  # need to get directory where PHA2 file is located
            resp_list_par = glob.glob(
                f"{pha_dir}/tg/{pha_root}*.{resp_type_par}"
            )  # use the root name of the PHA2 file to ID the responses. This way users can have many extractions in a 
               # single dir but it will only grab the appropriate ones.

    # if the creator of the PHA2 file is not DS or CIAO then exit.
    else:
        raise ValueError(
            "Cannot determine the creator of PHA2 file and responses will have to be loaded manually"
        )

    # check to make sure at least some files were found
    if len(resp_list_par) < 1:
        raise ValueError(
            "Could not identify responses. Please load responses manually."
        )

    # check that the length of the arf or RMF lists match the number of PHA spec in the PHA2 file
    if len(resp_list_par) != num_spec_par:
        print(
            f"WARNING-- The identified number of {resp_type_par.upper()}s [{len(resp_list_par)}] does not match the number of PHA spectra [{num_spec_par}] in the PHA2 file. Only the responses found will be included.\n"
        )

    return resp_list_par


def match_resp_order(pha2_file_par, resp_list_par, resp_type_par):
    """
    This uses the PHA2 file structure and matches the input response file list/array (resp_list_par) to the appropriate
    PHA2 spectrum using the header keywords tg_m, tg_part and obsid. This function is designed to take the output of
    find_resp_files() and put them in order of the PHA2 spectra.

    Parameters
    ----------

    pha2_file_par : PHA2 fits file
         PHA2 spectrum which is typically provided in the chandra archive of a downloaded HETG observation or after
         running chandra_repro on a chandra HETG obsID.
    resp_type_par: 'arf' or 'rmf'
        The type of response files for matchign to PHA spectra
    resp_dir_par: directory
        The directory where the HETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.

    Returns
    ----------

    matched_resp_list_par: array
        Returns an array of ARF or RMF file paths matched to the order (arrangement) of the input PHA2 file. The string
        value 'no match' is returned for elements where there is a spectrum in the PHA2 file but no matching response
        file.

    """

    # check to make sure responses are either arf or rmf
    if resp_type_par != "arf" and resp_type_par != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # reads in the pha2 file and checks how many spectra (orders) it includes.
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)

    # identify the file arrangement of the HETG orders and HEG/MEG arms via the PHA2 file
    tg_m_arr = spec_crate_par.TG_M.values
    tg_part_arr = spec_crate_par.TG_PART.values
    tg_obsid = get_keyval(spec_crate_par, "OBS_ID")

    # determine the number of spectra in the pha2 file based on the length of one of the tg arrays:
    num_spec_pha2 = len(tg_m_arr)

    # warn user if the number of PHA2 spectra are different than the number of response files (either found 
    # automatically or provided manually)
    if len(resp_list_par) != num_spec_pha2:
        print(
            f"\nWARNING -- The number of {resp_type_par} files [{len(resp_list_par)}] does not equal the number of spectra in the PHA2 file [{num_spec_pha2}]. Only responses that match with a spectrum will be included.\n"
        )

    # create empty lists to later append HEG/MEG arm, order and obsID values from the response files headers
    resp_m_arr = []
    resp_tg_part_arr = []
    resp_obsid_arr = []

    # read each response file and append appropriate header value
    for i in range(0, len(resp_list_par)):
        resp_data = read_file(resp_list_par[i])
        resp_m_arr.append(get_keyval(resp_data, "TG_M"))
        resp_tg_part_arr.append(get_keyval(resp_data, "TG_PART"))
        resp_obsid_arr.append(get_keyval(resp_data, "OBS_ID"))

    # convert obsid lists to numpy arrays for later use with np.where() for obsID checking
    tg_obsid = np.array(tg_obsid)
    resp_obsid_arr = np.array(resp_obsid_arr)

    # create an empty object array the same size as the PHA2 file (number of spectra) to hold either 'no match' or the 
    # path to the matched response file
    matched_resp_list_par = np.array([""] * num_spec_pha2, dtype="object")

    # for each spectra, use tg_m, tg_part and obsID to match to a single response file. Print appropriate errors.
    for i in range(0, num_spec_pha2):
        match_resp = np.where(
            (resp_m_arr == tg_m_arr[i])
            & (resp_tg_part_arr == tg_part_arr[i])
            & (resp_obsid_arr == tg_obsid)
        )[0].tolist()
        if len(match_resp) == 1:
            matched_resp_list_par[i] = resp_list_par[
                match_resp[0]
            ]  # this is the element in the response array that match the i_th element of the PHA2 file.
        elif len(match_resp) > 1:
            raise ValueError(
                f"ERROR, more than one {resp_type_par.upper()} match found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}. "
            )
        elif len(match_resp) == 0:
            matched_resp_list_par[i] = "no match"
            print(
                f"Warning, no {resp_type_par.upper()} found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}."
            )
        else:
            raise ValueError(
                f"ERROR - Something with wrong identifying {resp_type_par.upper()}s for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}"
            )

    # report the files matched to the screen in a nice format so it is clear it worked or didn't work
    print("\nThe following response files were found\n")

    # name the arm and order something more readable for output message
    arm = lambda x: "HEG" if x == 1 else "MEG" if x == 2 else "ERROR"
    order = lambda x: f"+{x}" if x > 0 else f"-{-1*x}" if x < 0 else "ERROR"

    print()
    for i in range(0, num_spec_pha2):
        print(
            f"{arm(tg_part_arr[i])+order(tg_m_arr[i])} -- {resp_type_par.upper()}: {matched_resp_list_par[i]}"
        )
    print()

    # returns the array of matched responses in the same order as the PHA2 spectra
    return matched_resp_list_par