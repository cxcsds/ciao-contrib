import numpy as np
import glob
from pathlib import Path
from sherpa.astro.ui import load_data, load_arf, load_rmf
from pycrates import read_file, get_keyval, read_pha, get_history_records, is_pha_type2


def find_resp_files(pha2_file, resp_type, resp_dir=None):
    """
    Identifies ARFs and RMFs that are associated with an HETG/LETG PHA2 file.

    Parameters
    ----------

    pha2_file : str
        Path to a PHA2 fits file which is typically provided in the chandra archive of a downloaded HETG/LETG observation or after
        running chandra_repro on a chandra HETG/LETG obsID.
    resp_type: 'arf' or 'rmf'
        The type of response files for matching to PHA spectra
    resp_dir: str
        The path to a directory where the HETG/LETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.

    Returns
    --------
    resp_list: list
        Returns a list of ARF or RMF files found.

    """

    # if user enters 'ARF' or 'RMF' then lower case for later glob use
    resp_type = resp_type.lower()

    # check to make sure responses are either arf or rmf
    if resp_type != "arf" and resp_type != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # load the pha2 file and obtain the crate where relevant information is stored
    pha2_dataset = read_pha(pha2_file)

    # Return Error if file is not a PHA2 file
    if is_pha_type2(pha2_dataset) != True:
        raise ValueError("Input file must be of type PHA2.")

    # grab the spectrum crate to determine tg_m and various header values
    spec_crate = pha2_dataset.get_crate(2)

    # identify the number of spectra in the PHA2 file
    num_spec = len(spec_crate.TG_M.values)

    # determine which pipeline the PHA2 file came from (archive vs CIAO user / tgcat download)
    creator_key = get_keyval(spec_crate, "CREATOR")

    if "Version DS" in creator_key:

        # if users pha2_file is a long path or a single file, strip the name and check for the root so the resp
        # glob doesn't get any extra unrelated files in the response dir.

        # Note, the strings in this section are based on the DS (CXC Data Systems Group) standard naming.
        pha_name = Path(pha2_file).name
        pha_root = pha_name.partition("_pha2.fits")[0]

        # uses provided resp_dir to check for files. First check for ARF/RMF.fits and if not found then check compressed.
        if resp_dir is not None:  # use provided resp_dir
            resp_list = glob.glob(
                f"{resp_dir}/{pha_root}*{resp_type}*.fits"
            )
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{resp_dir}/{pha_root}*{resp_type}*.fits.gz"  # will grab fits.gz files
                )

        # if user does not provide a response directory
        else:
            pha_dir = Path(
                pha2_file
            ).parent  # need to get directory where PHA2 file is located
            resp_list = glob.glob(
                f"{pha_dir}/responses/{pha_root}*{resp_type}*.fits"
            )
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{pha_dir}/responses/{pha_root}*{resp_type}*.fits.gz"  # will grab fits.gz files
                )

    elif (
        "Version CIAO" in creator_key
    ):  # this is produced via chandra_repro or user custom spectral extraction

        # read the header to search for the PHA2 root name which is often the same root as the responses
        hist = get_history_records(spec_crate)
        pha_root = ""  # set to "" (blank) so it still works for TGCAT downloaded data which has no root par.

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

        # if pha_root is not set then it means the file came from a tgcat downloaded PHA2 file.
        # TGCAT files also do not include '.fits' so have to only check resp_type or .gz

        # use glob and pha_root to find the responses
        if resp_dir != None:  # use provided resp_dir
            resp_list = glob.glob(f"{resp_dir}/{pha_root}*.{resp_type}")
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{resp_dir}/{pha_root}*.{resp_type}*"
                )  # will grab .gz files

        # if user does not provide response directory
        else:
            pha_dir = Path(
                pha2_file
            ).parent  # need to get directory where PHA2 file is located
            resp_list = glob.glob(f"{pha_dir}/tg/{pha_root}*.{resp_type}")
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{pha_dir}/tg/{pha_root}*.{resp_type}*.gz"  # will grab .gz files
                )
            # TGCAT does not come with a tg directory so check in the pha_dir for response files.
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{pha_dir}/{pha_root}*.{resp_type}"  
                )
            if len(resp_list) == 0:
                resp_list = glob.glob(
                    f"{pha_dir}/{pha_root}*.{resp_type}*.gz"  # will grab .gz files
                )

    # if the creator of the PHA2 file is not DS or CIAO then raise error and exit.
    else:
        raise ValueError(
            "Cannot determine the creator of PHA2 file and responses will have to be loaded manually"
        )

    # check to make sure at least some files were found
    if len(resp_list) == 0:
        raise ValueError(
            "Could not identify responses. Please load responses manually."
        )


    # check that the length of the ARF or RMF lists match the number of PHA spec in the PHA2 file
    if len(resp_list) != num_spec:
        print(
            f"\nWARNING-- The identified number of {resp_type.upper()}s [{len(resp_list)}] does not match the number of PHA spectra [{num_spec}] in the PHA2 file. Only the responses found will be included.\n"
        )

    return resp_list


def match_resp_order(pha2_file, resp_list, resp_type, verbose=False):
    """
    Matches each response to the appropriate spectrum.

    This uses the PHA2 file structure and matches the input response file list/array (resp_list) to the appropriate
    PHA2 spectrum using the header keywords tg_m, tg_part and obsid. This function is designed to take the output of
    find_resp_files() and put them in order of the PHA2 spectra.

    Parameters
    ----------

    pha2_file : str
        Path to a PHA2 fits file which is typically provided in the chandra archive of a downloaded HETG/LETG observation or after
        running chandra_repro on a chandra HETG/LETG obsID.
    resp_type: 'arf' or 'rmf'
        The type of response files for matchign to PHA spectra
    resp_dir: str
        The path to a directory where the HETG/LETG response files associated with the PHA2 file are located. If none provided, it
        will attempt to search for them.
    verbose: bool, optional
        If 'True' then the matched response files to each spectrum will be printed to the screen. The default is 'False'.

    Returns
    ----------

    matched_resp_list: array
        Returns an array of ARF or RMF file paths matched to the order (arrangement) of the input PHA2 file. The string
        value 'no match' is returned for elements where there is a spectrum in the PHA2 file but no matching response
        file.

    """

    # check to make sure responses are either arf or rmf
    if resp_type != "arf" and resp_type != "rmf":
        raise ValueError("Response type must be either arf or rmf")

    # reads in the pha2 file and checks how many spectra (orders) it includes.
    pha2_dataset = read_pha(pha2_file)
    spec_crate = pha2_dataset.get_crate(2)

    # identify the file arrangement of the HETG/LETG orders and HEG/MEG arms via the PHA2 file
    pha2_tg_m_arr = spec_crate.TG_M.values
    pha2_tg_part_arr = spec_crate.TG_PART.values
    pha2_tg_obsid = get_keyval(spec_crate, "OBS_ID")

    # determine the number of spectra in the pha2 file based on the length of one of the tg arrays:
    num_spec_pha2 = len(pha2_tg_m_arr)

    # create empty lists to later append HEG/MEG arm, order and obsID values from the response files headers
    resp_m_arr = []
    resp_pha2_tg_part_arr = []
    resp_obsid_arr = []

    # start a counter to determine how many response files are missing an OBS_ID header value
    obsid_missing_count = 0

    #NOTE -- The various try and excepts below are due to TGCat provided RMFs not having standard ciao header keywords as 
    # of 3/23/26. TGCat ACIS HETG RMFs do not have OBS_ID and TGCat HRC LETG RMFs do not have tg_part or tg_m keywords. 
    # The archive and repro RMFs do not have this problem.
    
    # read each response file and append appropriate header values
    for i in resp_list:

        #load the response file
        resp_data = read_file(i)
        
        #identify the gratings order
        try:
            resp_m_arr.append(get_keyval(resp_data, "TG_M"))
        except:
            resp_m_arr.append(get_keyval(resp_data, "ORDER"))
        
        #identify the gratings type (HEG, MEG or LEG).
        try:
            resp_pha2_tg_part_arr.append(get_keyval(resp_data, "TG_PART"))
        except:
            grating_type = get_keyval(resp_data, "GRATING")
            if grating_type == 'LETG':
               resp_pha2_tg_part_arr.append(3) #note LEG --> tg_part = 3
            else:
                raise ValueError(
                    f"ERROR-- Could not identify grating type and/or order. Please load responses manually.")           
        
        #identify the obsID
        try:
            resp_obsid_arr.append(get_keyval(resp_data, "OBS_ID"))
        except:
            resp_obsid_arr.append(pha2_tg_obsid)
            obsid_missing_count = obsid_missing_count + 1

    # if any number of response files don't have an obsID parameter then warn the user this wont be used to check. Still
    # continue though because this requirement is likely to almost never be an issue.
    if obsid_missing_count > 0:
        print(
            f"\nWARNING -- Header keyword OBS_ID is missing from {obsid_missing_count} {resp_type.upper()} file(s). {resp_type.upper()}(s) will not be checked against obsID for validity. \n"
        )

    # convert obsid lists to numpy arrays for later use with np.where() for obsID checking
    pha2_tg_obsid = np.array(pha2_tg_obsid)
    resp_obsid_arr = np.array(resp_obsid_arr)

    # create an empty object array the same size as the PHA2 file (number of spectra) to hold either 'no match' or the
    # path to the matched response file
    matched_resp_list = np.array([""] * num_spec_pha2, dtype="object")

    # for each spectrum in the PHA2 file, use tg_m, tg_part and obsID to match to a single response file. Print appropriate errors.
    for i in range(0, num_spec_pha2):
        match_resp = np.where(
            (resp_m_arr == pha2_tg_m_arr[i])
            & (resp_pha2_tg_part_arr == pha2_tg_part_arr[i])
            & (resp_obsid_arr == pha2_tg_obsid)
        )[0].tolist()
        if len(match_resp) == 1:
            matched_resp_list[i] = resp_list[
                match_resp[0]
            ]  # this is the element in the response array that match the i_th element of the PHA2 file.
        elif len(match_resp) > 1:
            raise ValueError(
                f"ERROR, more than one {resp_type.upper()} match found for TG_M={pha2_tg_m_arr[i]}, TG_PART={pha2_tg_part_arr[i]} and obsID={pha2_tg_obsid}. "
            )
        elif len(match_resp) == 0:
            matched_resp_list[i] = "no match"

    if verbose is True:
    # report the files matched to the screen in a nice format so it is clear it worked or didn't work
        print(
            f"\nThe following {resp_type.upper()} response files were found for obsID {pha2_tg_obsid}\n"
        )

        # name the arm and order something more readable for output message
        arm = {1: 'HEG', 2: 'MEG', 3: 'LEG'}

        for i in range(0, num_spec_pha2):
            print(
                f"{arm[pha2_tg_part_arr[i]]}{pha2_tg_m_arr[i]:+} -- {resp_type.upper()}: {matched_resp_list[i]}"
            )
        print() #add one extra line to separate load_hetg_resp text from sherpa text

    # check if no responses matched and report to user. Most common issue would be the OBSID parameter is wrong
    if (matched_resp_list == "no match").all():
        print(
            f"\nERROR -- No {resp_type.upper()} files matched the PHA2 spectra. Check that the ARFS and RMFs are from the same obsID. {resp_type.upper()} responses were not loaded.\n"
        )

    # returns the array of matched responses in the same order as the PHA2 spectra
    return matched_resp_list


def load_gratings_pha2(pha2_file=None, arf_dir=None, rmf_dir=None, dataset_id_start=1, use_errors=False, verbose=False):
    """
    Loads the HETG/LETG PHA2 spectrum and responses into the sherpa session.
    
    This function loads an HETG/LETG PHA2 file and any associated ARF and RMF response files. If matching responses are
    found only for a subset of HETG/LETG orders (e.g., orders +1 and -1) then only those order's responses will be loaded.
    This works only for PHA2 files and not PHA files. If arf_dir or rmf_dir are not provided then this tool will
    search for the responses in subdirectories where the PHA2 file is located using standard CIAO directory naming
    formats.

    Example
    -------
    >>> load_gratings_pha2(pha2_file="16370/repro/acisf16370_repro_pha2.fits", dataset_id_start=1)
    >>> load_gratings_pha2("pha2_file=16371/repro/acisf16371_repro_pha2.fits", dataset_id_start=13)

    Parameters
    ----------

    pha2_file : str
         Path to a PHA2 fits file which is typically provided in the chandra archive of a downloaded HETG/LETG observation or after
         running chandra_repro on a chandra HETG/LETG obsID.
    arf_dir: str
        The path to a directory that holds the arfs associated with the pha2_file
    rmf_dir: str
        The path to a directory that holds the rmfs associated with the pha2_file
    dataset_id_start: int
        A sherpa dataset id into which PHA2 spectra will begin loading. A typical HETG/LETG PHA2 spectral file contains
        12 individual spectra so choosing a value 1 (default) will load dataset ids 1-12.
    use_errors: bool, optional
        If 'True' then the statistical errors are taken from the input data, rather than calculated by Sherpa from 
        the count values. The default is 'False'. 
    verbose: bool, optional
        If 'True' then the matched response files to each spectrum will be printed to the screen. The default is 'False'.         

    Related Sherpa functions
    ------------------------
    show_data : Display information on the data sets that have been loaded.
    list_data_ids : List the identifiers for the loaded data sets.
    show_all : Display information about one or all of the data sets that have been loaded into the Sherpa session.

    """
    # run find_resp_files() and match_resp_order() and load data into appropriate dataset id.

    # find and match ARFs
    arf_list = find_resp_files(
        pha2_file=pha2_file, resp_type="arf", resp_dir=arf_dir
    )
    arf_list_matched = match_resp_order(
        pha2_file=pha2_file, resp_list=arf_list, resp_type="arf", verbose=verbose
    )

    # find and match RMFs
    rmf_list = find_resp_files(
        pha2_file=pha2_file, resp_type="rmf", resp_dir=rmf_dir
    )
    rmf_list_matched = match_resp_order(
        pha2_file=pha2_file, resp_list=rmf_list, resp_type="rmf", verbose=verbose
    )

    # check for mismatches and unmatched pairs
    if len(arf_list) != len(rmf_list):
        raise ValueError(
            "The number of ARFs and RMFs identified do not match. Please manually load matching responses"
        )

    if len(arf_list_matched) != len(rmf_list_matched):
        raise ValueError(
            "Something went wrong matching responses to the PHA2 file. Please manually load responses."
        )

    # convert dataset_id_start to an integer if users enters it as a string.
    if type(dataset_id_start) == str:
        dataset_id_start = int(dataset_id_start)

    # load data first so responses can be assigned after.
    load_data(id=dataset_id_start, filename=pha2_file, use_errors=use_errors)

    # for every identified response (arf), load matching arf and rmf. It should be ok to load RMFs with the arf loop
    # cause an error would be previously thrown if every arf didn't have a matching rmf.
    for i in range(len(arf_list_matched)):
        if arf_list_matched[i] != "no match":
            # note, i+dataset_id_start here cause sherpa starts with dataset 1 and not 0.
            load_arf(i + dataset_id_start, arf_list_matched[i])
            load_rmf(i + dataset_id_start, rmf_list_matched[i])

    return
