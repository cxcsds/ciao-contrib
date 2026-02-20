#See README.me for general info about CrissCross

#List of things I still need to do:

    #add back in ds9 figure generation so users can see where confusion occurs on the evt2 fits image.

    #create tutorial for using code with a simple case

    #add functionality for user to calculate confusion between two selected sources in a field of view and print results to screen.

    #spec_flag_set takes a lot of time to run and should be made more efficient.

    #format code to fix character limit to < 120 characters

##########################################################################################
##########################################################################################
##########################################################################################

import numpy as np
import matplotlib.pyplot as plt
import os
import math
import glob
import shutil
from ciao_contrib.runtool import *
import time 
from iocaldb import OSIP, Sky2Chandra, Cel2Chandra
from widthofexclusion import *
from pycrates import read_file, write_file, TABLECrate, CrateData, add_col, add_record, get_keyval, read_pha, write_pha, is_pha_type1, is_pha_type2, update_crate_checksum, get_history_records, set_key
from crates_contrib.utils import make_table_crate
import csv
from pathlib import Path

############################################################


#############FUNCTION DEFINITIONS###############


def make_output_dir(cc_outdir, obsid_par, clobber_par=False):
    """
    Creates a CrissCross directory to hold all output. Each obsID will get its own subdir. Reports back to main 
    function if output dir exists so it can exit without removing if clobber=False.

    Parameters
    ----------
    cc_outdir : str
        directory name or path to hold all CrissCross output.
    obsid_par : str
        obsID value of the observation used for naming subdirectory.
    clobber_par : bool
        boolean which is set by main function to determine whether cc subdirs should be clobbered when run. 
    """
    #create a subdir for each obsID run
    output_dir = f'{cc_outdir}/output_dir_obsid_{obsid_par}'
    
    if os.path.isdir(output_dir):
        already_exists = True
    else:
        already_exists = False

    #if an output directory for this obsID already exists then delete it first
    if clobber_par == True and already_exists == True:
        shutil.rmtree(output_dir)
    
    os.makedirs(cc_outdir, exist_ok = True)
    os.makedirs(output_dir, exist_ok = True)

    return(output_dir, already_exists)



def get_header_par(fits_file, keyword_par):
    """
    Retrieves header keyword value

    Parameters
    ----------
    fits_file : str
        fits file which holds the relevant header keyword
    keyword_par : str
        header keyword value to retrieve
    """

    dmkeypar.punlearn()
    a = dmkeypar(infile=fits_file, keyword=keyword_par)
    return_val = dmkeypar.value

    return(return_val)


#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#See wavedetect open question at top 
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
def run_wavdetect(evt2_file=None, outdir=None, outroot='sdetect', binsize=2.0, bands='broad', psfecf=0.9, verbose=0, clobber='yes'):
    """
    Performs source detection on an obsID with the goal of determining the number of 0th order counts for each 
    source in field. The only file used in CrissCross by this function is the wavdetect.outfile source detection table.
    This function is run if user does not provide source table. Function runs fluximage and wavdetect on an evt2 file
    and requires a evt2 directory setup such that the ancillary ACIS files can be automatically found by CIAO.

    Parameters
    ----------
    evt2_file : str
        event file for running the source detection.
    outdir : str
        directory for holding the wavdetect output.
    outroot : str
        root for naming wavdetect output.
    binsize : float
        CIAO tool fluximage parameter binning factor. binsize=4 corresponds to 1.968 arcseconds pixels for ACIS.
    bands : str 
        CIAO tool fluximage par denoting the energy bands used for exposure-corrected images. See band definitions in 
        the CSC documentation. Example options are 'broad': 0.5-7.0 keV with eff E of 2.3 keV, 'soft','medium','hard'.
    psfecf : float
        fluximage par for creating a PSF map with the provided encircled energy fraction.
    verbose : int
        CIAO verbose level for printing log to screen.
    clobber : bool
        CIAO clobber value to overwrite files.
    """

    print(f'\nNo input wavdetect source fits table provided so running wavdetect on {evt2_file} with binsize={binsize}, bands={bands} and psfecf={psfecf}.') 
    print('If you wish to use other wavdetect parameters please run wavdetect and provide a wavdetect source fits table.\n')

    fluximage.punlearn()
    fluximage.infile=evt2_file
    fluximage.outroot=f'{outdir}/{outroot}'
    fluximage.binsize=binsize
    fluximage.bands=bands
    fluximage.psfecf=psfecf
    fluximage.verbose=verbose
    fluximage.clobber='yes'

    fluximage()

    wavdetect.punlearn()
    wavdetect.infile=f'{outdir}/{outroot}_{bands}_thresh.img'
    wavdetect.psffile=f'{outdir}/{outroot}_{bands}_thresh.psfmap'
    wavdetect.outfile=f'{outdir}/{outroot}_src.fits'
    wavdetect.scellfile=f'{outdir}/{outroot}_scell.fits'
    wavdetect.imagefile=f'{outdir}/{outroot}_imgfile.fits'
    wavdetect.defnbkgfile=f'{outdir}/{outroot}_nbgd.fits'
    wavdetect.regfile=f'{outdir}/{outroot}_src.reg'
    wavdetect.verbose=verbose
    wavdetect.clobber=clobber

    wavdetect()

    return(f'{outdir}/{outroot}_src.fits')


def wavedetect_match_obsid(fits_list_par, wavdetect_list_par):
    """
    Uses the obsID header value from the evt file (fits_list) and wavedetect source tables (wavedetect_list)
    to reorder the wavdetect_list to match the evt2_list. If users provide a list of evt2 and wavdetect source tables
    then this function ensures they are not mis-matched when running in CrissCross.

    Parameters
    ----------
    fits_list_par : str
        a single evt2 filename or a list of evt2 file names.
    wavdetect_list_par : str
        a single wavdetect output source table or a list of them.
    """

    fits_obsid = []
    wave_obsid = []

    wavedetect_sorted = []

    for i in range(0,len(fits_list_par)):
        wave_obsid.append(get_header_par(fits_file = wavdetect_list_par[i], keyword_par = 'obs_id'))
        fits_obsid.append(get_header_par(fits_file = fits_list_par[i], keyword_par = 'obs_id'))

    for i in range(0,len(fits_list_par)):
        for j in range(0,len(wave_obsid)):
            if fits_obsid[i] == wave_obsid[j]:
                wavedetect_sorted.append(wavdetect_list_par[j]) 

    return(wavedetect_sorted)
    


def load_sourcelist(filename=None, subset_list=False):
    """
    Load an ascii, tsv or fits file with RA, DEC and ID columns using pycrates. If an ID column is not found for the 
    full list of field sources then and ID column is generated. The file is expected to have a header column 
    of #RA DEC ID. If it does not then the first two columns read in will be treated as RA and DEC and a warning 
    message is printed to screen. This function is used for both the main source list and the subset list. The subset
    list must be matched to the main_list source ID (or element number) using match_subset_to_main().

    Parameter
    ---------
    filename = str
        ascii, tsv or fits table with RA, DEC and ID columns.
    subset_list = bool
        Boolean denoting whether this function is to be run on the main list of sources or the subset list of sources.
    """

    if filename != None:
        #default to setting a flag to no generate the ID column
        gen_id = False
        
        #read the data file in and get info about columns
        cratedata = read_file(filename)
        colnames = cratedata.get_colnames()
        crate_len = len(colnames)

        #check to see if user forgot to put hash in front of column header which woudl result in crate being type <U17
        if cratedata.get_column(colnames[0]).values.dtype == '<U17':
            raise TypeError('\nFirst row of file cannot be of string format. If header columns are present please ensure # is first character of line.\n')

        elif crate_len < 2:
            raise TypeError(f'\nERROR reading "{filename}". Please ensure file type is ascii or tsv and there are at least two columns (RA DEC) in degrees\n')
        
        #if len=2 then probably only RA and DEC present. For the subset_list, do NOT create new ID values because they must match the main_list IDs.
        elif crate_len == 2 and subset_list == False:
            print(f'No ID column found so IDs will be generated from 0 to length of file')
            gen_id = True

        #if len=3 the prob RA, DEC, ID so check ID column to make sure they can be converted to integers necessary for naming purposes
        elif crate_len == 3:
            
            idcol_test = cratedata.get_column(colnames[2]).values
            try:
                idcol_test.astype(int)
            except:
                raise TypeError('Third column of input file need to be integers')
                
            if len(np.unique(idcol_test)) != len(idcol_test):
                raise TypeError('ID column does not contain unique identifier for each source')
            
            if colnames[2] != 'ID' and colnames[2] != 'id':
                print(f'Warning -- Column 2 of "{filename}" is not ID or id. Assuming it is ID from now on.')

        else:
            print(f'File "{filename}" contains more than three columns and the rest will be ignored.')

        #check if the first two columns have typical names of RA and DEC otherwise warn.
        if colnames[0] != 'RA' and colnames[0] != 'ra':
            print(f'Warning -- Column 1 of "{filename}" is not RA or ra. Assuming it is RA from now on.')
        if colnames[1] != 'DEC' and colnames[1] != 'dec':
            print(f'Warning -- Column 2 of "{filename}" is not DEC or dec. Assuming it is DEC from now on.')

        RA = cratedata.get_column(colnames[0]).values
        DEC = cratedata.get_column(colnames[1]).values
        if gen_id == True:
            ID = np.arange(0, len(RA))
        elif subset_list == False:
            ID = cratedata.get_column(colnames[2]).values.astype(int)

        if subset_list == False:            
            return(RA, DEC, ID)
        elif subset_list == True:
            return(RA, DEC)
        else:
            raise ValueError('Something went wrong with subset_list truth value.')
    else:
        raise ValueError('CrissCross needs to be run with a list of known sources RA and DEC.')


def match_subset_to_main(RA_main, DEC_main, RA_sub, DEC_sub, round_sig = 6):
    """
    Matches sources from the subset_list to the main_list by RA and DEC. All sources in the subset list MUST be also in
    the main list and matched via the element number of the input main_list array. For example, if source number 10 in
    the subset_list (row 10) is the same source as row 200 in the main_list, then source 10 will be matched with 
    element 200 and CrissCross will use e.g. src_pos_x[200], src_pos_y[200] when handling subset_list source 10. If 
    no or multiple matches are found for a single source then error is thrown. Every source must be unique.

    Parameters
    ----------
    RA_main : float, deg
        Right Ascension of main_list source in J2000 degrees
    DEC_main : float, deg
        Declination of main_list source in J2000 degrees
    RA_sub : float, deg
        Right Ascension of subset_list source in J2000 degrees
    DEC_sub : float, deg
        Declination of main_list source in J2000 degrees
    round_sig : int
        Number of digits to round RA/DEC to for matching purposes. 
    """

    element = [None] * len(RA_sub)
    # for each source in the subset_list match it using RA and DEC to a source in the main_list. Check for mult matches
    for i in range(0,len(RA_sub)):
        element[i] = np.where((np.round(RA_sub[i],round_sig) == np.round(RA_main,round_sig)) & (np.round(DEC_sub[i],round_sig) == np.round(DEC_main,round_sig)))[0]
        if len(element[i]) == 0:
            raise ValueError(f'No match in main list found for subset source RA={RA_sub[i]} and DEC={DEC_sub[i]}. Please make sure RA and DEC value of source to clean matches a source in main_list.')
        
        elif len(element[i]) >1:
            raise ValueError(f'Multiple matches [{len(element[i])}] in main list found for subset source RA={RA_sub[i]} and DEC={DEC_sub[i]}. Please make sure there are no duplicate entries in main list or subset_list')
        #strip array to provide only integer value
        else:
            element[i] = element[i][0]

    return(element)


def calc_physical_coords(fits_par, RA_par, DEC_par):
    """
    Converts from RA and DEC in WCS degrees to Chandra physical coordinates. This also determines the off-axis angle
    and converts it to arcseconds.

    Parameters
    ----------
    fits_par : str
        evt2 fits file.
    RA_par : str
        Right ascension in degrees.
    DEC_par : str
        Declination in degrees.
    """
    
    cel_convert = Cel2Chandra(fits_par)

    pos_x_par = np.zeros(len(RA_par))
    pos_y_par = np.zeros(len(DEC_par))
    off_axis_ang = np.zeros(len(RA_par))

    for i in range(0,len(RA_par)):
        a = cel_convert(RA_par[i], DEC_par[i])
        pos_x_par[i] = a['x'][0]
        pos_y_par[i] = a['y'][0]
        off_axis_ang[i] = a['theta'][0] * 60.0 #convert from arcmin to arcsec

    return(pos_x_par, pos_y_par, off_axis_ang)


def find_closest_source(src_x, src_y, wave_file, max_offset = 3.0):
    """
    Matches sources from the main_list to the wavdetect source table with the goal of removing erroneous 
    disperssed-grating-line sources. Wavdetect is not meant to be run on HETG observations and thus will include many 
    'false' detections from the dispersed spectra. This identifies the closest matching source in a group to a single 
    source based on Chandra SKY physical coordinates only. If multiple matches are found for a single source within 
    max_offset, only the closest of the matches is assigned to the source. This avoids 'double counting'. This returns
    the number of NET_COUNTS associated with 0th order (non-dispersed) detections. NET_COUNTS are used throughout 
    CrissCross to determine the severity of confusion.
    
    Parameters
    ----------
    src_x : float, array
        src x position in Chandra physical units.
    src_y : float, array
        src y position in Chandra physical units.
    wave_file : str
        path to wavdetect output source fits table.
    max_offset : float
        The max distance in arcsec two sources can be before they are no longer considered matchable between the source
        list and the wavdetect table. All sources are treated the same regardless of off-axis angle which is generally
        ok because centroids should be relatively good as determined by wavdetect.
    """


    #ACIS parameters for converting distance from pixels to arcseconds
    acis_platescale = 48.82E-6 #meters/arcsec
    acis_pix_size = 24E-6 #meters / pixel (square pixels)
    acis_arcsec_per_pix = acis_pix_size / acis_platescale

    #read in and assign relevant wavdetect columns
    wave_data = read_file(wave_file)

    src_wave_x_arr = wave_data.POS.X.values
    src_wave_y_arr = wave_data.POS.Y.values
    counts_wave = wave_data.NET_COUNTS.values

    closest_dist_arr = np.empty(len(src_x), dtype='float') #holds the distance in arcsec to the closest matching source from the wavedetect table
    closest_match_arr = np.empty(len(src_x), dtype='int') #holds the index value from the wavedetect table that is the closest match to a source in the source list.
    
    #these will hold the values above for the matched source AFTER you remove double matches and sources > max_offset.
    final_match_arr = np.empty(len(src_x), dtype=object)
    final_dist_arr = np.empty(len(src_x), dtype=object)

    matched_0th_counts_arr = np.empty(len(src_x), dtype='float') #the final 0th_order counts array (NET_COUNTS) from the wavedetect table MATCHED to the user-provided source list.

    #this loop determines the distance from the user-provided source to ALL the sources in the wavedetect table and only saves a non-bogus value if there is a source with separation < max_offset.
    for i in range(0,len(src_x)):
        
        dist_arr = []
        dist_arr = np.sqrt( (src_x[i] - src_wave_x_arr)**2 + ( src_y[i] - src_wave_y_arr)**2  ) #This calculates the physical distance from source [i] in the user-provided table to ALL sources in the wavedetect table. This is just the hypotenuse in the xy plane. Note, calculating the ENTIRE array here for each [i] source and NOT each [i] and each [j] individually. 
        
        closest_dist = []
        closest_dist = np.min(dist_arr) * acis_arcsec_per_pix #converted from sky coords to arsec

        #if distance is > max offset then assign values of 99999 (bogus) and filter out in next loop. Otherwise, assign matched values.
        if closest_dist <= max_offset:
            closest_dist_arr[i] =  closest_dist
            closest_match_arr[i] = np.where(dist_arr == np.min(dist_arr))[0][0] #
        else:
            closest_dist_arr[i] =  99999
            closest_match_arr[i] = 99999             

    #this loop will remove 'double counting' where a single user-provided source might match to multiple wavedetect sources. This will only match to the closest one and remove that from the pool of potential matches for other sources.
    for i in range(0,len(src_x)):
        
        common_matches = np.where(closest_match_arr == closest_match_arr[i])[0] #this will give an array of index values which all have the same closest matched source.
        common_matches_dist = closest_dist_arr[common_matches] #this will provide an array of all of the distances for the closest matched sources. The idea is that only the closest distance can be assigned to a single source (no double counting).

        if (closest_dist_arr[i] <= max_offset) and (closest_dist_arr[i] == np.min(common_matches_dist)): #if the current source's closest distance is the closest of all the common matches then it is 'correct' and assigned the wavedetect number of counts. Otherwise, counts are set to 0 (not detected)
            final_match_arr[i] = closest_match_arr[i]
            final_dist_arr[i] = closest_dist_arr[i]
            matched_0th_counts_arr[i] = counts_wave[closest_match_arr[i]]
        else:
            final_match_arr[i] = 'no match'
            final_dist_arr[i] = 'no match'            
            matched_0th_counts_arr[i] = 0     
    
    return(final_match_arr, final_dist_arr, matched_0th_counts_arr)



def write_matched_file(srcid_par, ra_par, dec_par, counts_par, fileroot = 'matched_source_list', output_type = 'txt'):
    """
    Creates a csv or txt file to save SrcID, RA, Dec and wave_detect_matched 0th order counts.

    Parameter
    ---------
    srcid_par : int, array
        source ID values from the input main_list.
    ra_par, dec_par : float
        J2000 Right ascension and declination taken from the input main_list
    counts_par : float
        The number of 0th order counts matched to each main_list source using the wavdetect source detection table.
    fileroot : str
        root for naming purposes
    output_type : str
        text file output type to save. Can be 'txt' or 'csv'.
    """

    filestack = np.column_stack((srcid_par, ra_par, dec_par, counts_par))

    if output_type == 'csv':
        np.savetxt(fileroot+'.csv', filestack, delimiter=',', fmt=['%d', '%.6f', '%.6f', '%.1f'], header = 'ID,RA,DEC,0th_counts', comments='') #need comments to get rid of extra # sign
    elif output_type == 'txt':
        np.savetxt(fileroot+'.txt', filestack, delimiter='\t', fmt=['%d', '%.6f', '%.6f', '%.1f'], header = 'ID,RA,DEC,0th_counts', comments='')
    else:
        raise ValueError('The only output types accepted are csv and txt.')

    return()


def determine_line_intersect_values(src_pos_x_par, src_pos_y_par, heg_ang_par, meg_ang_par):
    """
    Solves the equation where two lines (e.g., dispersed spectra) intersect on ACIS and saves relevant values for 
    use in later functions. This calculation is relevant to both spectral confusion and point source confusion.

    Parameter
    ---------
    src_pos_x_par, src_pos_y_par : float
        0th order source physical coordinates on ACIS.
    heg_ang_par, meg_ang_par : float
        The slope of the HEG and MEG arms on the detector converted to radians. Set by HETG instrument and roll angle.
    """

    #makes sure the grid values make it so nothing is negative when subtracting.
    xoff= int(np.min(src_pos_x_par) - 100)
    yoff=int(np.min(src_pos_y_par) - 100)

    #change coords to other grid to account for offset 
    src_pos_x_par_grid = (src_pos_x_par - xoff)
    src_pos_y_par_grid = (src_pos_y_par - yoff)

    #slope of a line m = (y2-y1)/(x2-x1) is same thing as tan(theta)  where theta = delta(y)/delta(x) so just knowing the angle ahead of time from Chandra's geometry via aciss and hetg gives us slope for each star --- 
    m_heg=np.tan(np.deg2rad(heg_ang_par))
    m_meg=np.tan(np.deg2rad(meg_ang_par))

    #since we know x, y, and now m for each target, we can calculate b for each one of the meg and heg arms (need both cause meg and heg have different angles)
    b_heg = (src_pos_y_par_grid - (m_heg*src_pos_x_par_grid))
    b_meg = (src_pos_y_par_grid - (m_meg*src_pos_x_par_grid))

    #This xintercept and yintercept gives the X and Y location where there is an intersection of gratings.  If two lines intersect each other, that means there is one point (the intersection point) where the X and Y values of BOTH lines will be the same.  Since we know the y=mx + b equation for each target now (see above), we can calculate the location two lines intersect by first equating their y values i.e., y1 = y2 --> m1x1+b1 = m2x2+b2.  Since X will also be the same value at this intersection, we can solve for X where m1X+b1 = m2X+b2 -->  X(m1-m2) = b2 - b1 or X = (b2-b1)/(m1-m2). e.g., xintercept_heg[0,1] is location where source 0's heg spectrum is intersected by source 1's meg spectrum.  Keep in mind the slopes m1 and m2 will be different. If they are the same they will not intersect cause parallel.

    xintercept_heg=np.zeros((len(src_pos_x_par),len(src_pos_x_par)))
    xintercept_meg=np.zeros((len(src_pos_x_par),len(src_pos_x_par)))

    for i in range (len(src_pos_x_par)):
        for j in range (len(src_pos_x_par)):
            xintercept_heg[i,j] = xoff + ((b_meg[j]-b_heg[i])/(m_heg-m_meg)) #note, this does where meg intersects heg; 
            xintercept_meg[i,j] = xoff + ((b_heg[j]-b_meg[i])/(m_meg-m_heg)) #note, this does where heg intersects meg
        
    #Once you solve for the X values (above), you can then plug those back in to solve for the Y values with y = mx+b
    #yintercept=yoff+((m1*(xintercept-xoff))+b1)

    yintercept_heg=np.zeros((len(src_pos_x_par),len(src_pos_x_par)))
    yintercept_meg=np.zeros((len(src_pos_x_par),len(src_pos_x_par)))

    for i in range (len(src_pos_x_par)):
        for j in range (len(src_pos_x_par)):
            yintercept_heg[i,j] = yoff + ((m_heg*(xintercept_heg[i,j]-xoff))+b_heg[i])
            yintercept_meg[i,j] = yoff + ((m_meg*(xintercept_meg[i,j]-xoff))+b_meg[i])

    return(m_heg, m_meg, b_heg, b_meg, xintercept_heg, xintercept_meg, yintercept_heg, yintercept_meg, xoff, yoff)


def conf_dict(num_sources, highest_order=3):
    """
    A nested dictionary that holds all of the relevant data for confusion between two sources for all sources in the
    main_list. Each MEG/HEG arm has 6 orders and, in a general sense, all orders from one arm can interact with all 
    orders from another arm. This nested dictionary was created to intelligently hold all of this information while 
    still being relatively readible. The format of this dictionary is: spec_confuse['arm+order'][parameter][i,j]
    where 'i' is the potentially CONFUSED source and 'j' is the potential CONFUSER source. For example, 
    spec_confuse['meg-1']['wave'][5,10] denotes the meg arm of srcID=5 (row 5 of main_list) has potential confusion
    in the '-1' order from the dispersed spectrum of SrcID=10 (row 10 of main_list). The 'wave' value in this example
    denotes the wavelength in angstrom where the spectral confusion occurs in the spectrum of SrcID 5. Both spectral
    confusion and point source confusion share this dictionary format but in separate variables.
    
    Parameters
    ----------
    num_source : int
        number of sources in the main_list
    highest_order : int
        the number of orders to calculate. WARNING, values other than 3 have not been fully tested.


    Dictionary key description
    --------------------------    
    ['intersec_dist'] : The distance in pixels along the grating arm between the 0th order src i and the 
        location where confusion may occur from source j.
    ['xintercept'] : The X location (physical coords) where there is an intersection of gratings between src i and j.
    ['yintercept'] : The Y location (physical coords) where there is an intersection of gratings between src i and j.
    ['flag'] : primary flag which represents potential sources of confusion for ALL orders between source i and j.
    ['flag comment'] : description denoting the origin of confusion for ALL orders between src i and j
    
    arm values : HETG arm values 'heg' or 'meg'        
    arm orders : HETG order values -3, -2, -1, +1, +2, +3  

    ['arm+order']['wave'] : the wavelength where confusion may occur in the spectrum of src i.
    ['arm+order']['wave_low'] : the lwoer bounds where confusion may occur
    ['arm+order']['wave_high'] : the upper bounds where confusion may occur
    ['arm+order']['osip_low'] : lower bounds of the OSIP window at the location where confusion may occur
    ['arm+order']['osip_high'] : upper bounds of the OSIP window at the location where confusion may occur
    ['arm+order']['flag'] : arm/order specific confusion flag 
    ['arm+order']['flag_comment'] : arm/order specific origin of confusion between src i and j
    """

    arms = ['heg', 'meg'] #arms will always be heg or meg
    arm_order = list() #create an empty list that gets appended with the arm+order

    order_arr = np.arange((-1 * highest_order), (highest_order+1)) #take the input highest order and make an array from (-highest_order to highest_order). Note, arange stops one early so must have +1
    order_list = list(order_arr) #convert the array to a list 
    order_list.remove(0) #remove '0' from the list 

    orders = list()

    for i in order_list:
        if i < 0:
            orders.append(str(i))
        if i > 0:
            orders.append('+'+str(i))

    for i in arms:
        for j in orders:
            arm_order.append(i+j) #combines the arm name and the order number to generate each dictionary key
    
    confusion_dict = {} #create an empty dictionary

    #for each arm+order, create empty arrays for wavelength and for flag		
    for k in arm_order:

        confusion_dict[k] = {'wave': np.zeros((num_sources,num_sources)), 'wave_low': np.zeros((num_sources,num_sources)), 'wave_high': np.zeros((num_sources,num_sources)), 'osip_low': np.zeros((num_sources,num_sources)), 'osip_high': np.zeros((num_sources,num_sources)), 'flag': np.full((num_sources,num_sources), 'unset', dtype=object), 'flag_comment': np.full((num_sources,num_sources), '', dtype=object)}

    #add intersection_distance for each arm **NOTE-- this does NOT depend on order therefore it gets its own dict reference here and its not embedded in the arm loop.
    confusion_dict['intersect_dist'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))}
    confusion_dict['xintercept'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))} 
    confusion_dict['yintercept'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))}

    #add main flag par - one that summarizes all arms to quickly identify if the extract source [i] has any confusion at all with another source [j]
    confusion_dict['flag'] = np.full((num_sources,num_sources), 'unset', dtype=object)
    confusion_dict['flag_comment'] = np.full((num_sources,num_sources), '', dtype=object)


    return(confusion_dict)





####SPECTRAL CONFUSION FUNCTIONS####


def spec_confuse_wave(spec_dict, src_pos_x, src_pos_y, armtype, xintercept, yintercept, counts, min_spec_counts, min_spec_confuser_counts, period_arm, highest_order, roll_nom_par, mm_per_pix, X_R):
    """
    Calculates the distance from the 0th order of src i to the location where confusion may occur ['intersect_dist'] 
    and converts that into wavelength in angstroms ['wave'] using the gratings equation.

    Parameters
    ----------
    spec_dict : dictionary
        spectral confusion dictionary which holds all possible spectral confusion entries for every source in main_list
    src_pos_x, src_pos_y : float
        Source position in physical coordinates.
    armtype : str
        HETG arm type of 'heg' or 'meg'.
    xintercept, yintercept : float
        x and y location on ACIS where spectral intersection occur between source i and j.
    counts : int
        number of 0th order counts.
    min_spec_counts, min_spec_confuser_counts : int
        CrissCross input parameter denoting the 0th order counts threshold to consider a source for spectral confusion.
    period_arm : float
        The period associated with the HEG or MEG gratings (instrumental constants)
    highest_order : int
        The highest HETG order to perform confusion check for. Warning, orders other than three are not sufficiently 
        tested.
    roll_nom_par : float
        The Chandra roll angle in degrees associated with the observation.
    """

    # #assign the x,y intercepts to the spec_dict. Note, this is done in sort of a weird way cause it was an after thought but for now it should stay. code below uses x/y intercept parameter instead of spec_dict[xyintercept]].
    if armtype == 'heg':
        spec_dict['xintercept']['heg'] = xintercept
        spec_dict['yintercept']['heg'] = yintercept

    if armtype == 'meg':
        spec_dict['xintercept']['meg'] = xintercept
        spec_dict['yintercept']['meg'] = yintercept			

    order_arr = np.arange(1, highest_order+1)

    if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
        for i in range (len(src_pos_x)):
            for j in range (len(src_pos_x)):		
                spec_dict['intersect_dist'][armtype][i,j] = np.sqrt( (src_pos_x[i]-xintercept[i,j])**2 + (src_pos_y[i]-yintercept[i,j])**2)
                if src_pos_x[i] != xintercept[i,j] and xintercept[i,j] > src_pos_x[i] and counts[i] > min_spec_counts and counts[j] > min_spec_confuser_counts: 
                    for k in order_arr:
                        spec_dict[armtype+'+'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_dict['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
                elif src_pos_x[i] != xintercept[i,j] and xintercept[i,j] < src_pos_x[i] and counts[i] > min_spec_counts and counts[j] > min_spec_confuser_counts:
                    for k in order_arr:
                        spec_dict[armtype+'-'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_dict['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number

    elif (roll_nom_par > 90 and roll_nom_par < 270):
        for i in range (len(src_pos_x)):
            for j in range (len(src_pos_x)):
                spec_dict['intersect_dist'][armtype][i,j] = np.sqrt( (src_pos_x[i]-xintercept[i,j])**2 + (src_pos_y[i]-yintercept[i,j])**2)
                if src_pos_x[i] != xintercept[i,j] and xintercept[i,j] < src_pos_x[i] and counts[i] > min_spec_counts and counts[j] > min_spec_confuser_counts: 
                    for k in order_arr:
                        spec_dict[armtype+'+'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_dict['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
                elif src_pos_x[i] != xintercept[i,j] and xintercept[i,j] > src_pos_x[i] and counts[i] > min_spec_counts and counts[j] > min_spec_confuser_counts:
                    for k in order_arr:
                        spec_dict[armtype+'-'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_dict['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
    else:
        print('Check ROLL_NOM value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')	


    return(spec_dict)




def spec_confuse_wave_bounds(spec_dict, highest_order, num_sources, heg_bound = 0.68, meg_bound = 1.33):

    """
    Sets the wave_low and wave_high spectral confusion windows for every source ASSUMING there is spectral confusion.
    Fixed distances based on the intersection geometry (which should be 120 pixels: 1.33 A for MEG and 0.68 A for HEG)
    are used instead of the OSIP bounds. This calculation is done for ALL sources but only those flagged with confusion 
    will be treated as such. The OSIP range is still used later to quantify how many spectral confusion counts lie in 
    the confusion region for flagging and then these smaller wave bounds are saved to the confusion tables.

    Parameters
    ----------
    spec_dict : dictioanry
        Spectral confusion dictionary which holds all possible spectral confusion entries for every source in main_list.
    highest_order : int
        Highest HETG order to perform confusion check for. Warning, orders other than three are not sufficiently tested.
    num_sources : int
        Number of sources in the main_list.
    heg_bound, meg_bound : float
        The size of the bandpass in Angstroms when converting from the number of pixels associated with HEG/MEG spectra
        intersecting.
    """
    #heg_bound and meg_bound are in units of Angstrom and represent the entire window (bounds). It is no recommended to go smaller than the default values as they are determined based on the intstrument.

    #need the keys AND the order numbers in string format
    keys_list = list(spec_dict.keys())
    keys_list.remove('intersect_dist')
    keys_list.remove('xintercept')
    keys_list.remove('yintercept')
    keys_list.remove('flag')
    keys_list.remove('flag_comment')

    for i in range(0,num_sources):	#loop through each instance of spectral confusion for each source
        for j in range(0,num_sources):
            for m in keys_list: #one of the keys is 'intersect' so I can't loop through just keys. I need to make sure I'm just looking through the arms (which have subkeys wave and flag)
            
                if spec_dict[m]['wave'][i,j] != 0 and i != j:	#only calculate wave_low and wave_high for sources that have a confusion wavelength calculated 
                    if 'heg' in m:
                        spec_dict[m]['wave_low'][i,j] = spec_dict[m]['wave'][i,j] - (heg_bound/2)
                        spec_dict[m]['wave_high'][i,j] = spec_dict[m]['wave'][i,j] + (heg_bound/2)
                    if 'meg' in m:
                        spec_dict[m]['wave_low'][i,j] = spec_dict[m]['wave'][i,j] - (meg_bound/2)
                        spec_dict[m]['wave_high'][i,j] = spec_dict[m]['wave'][i,j] + (meg_bound/2)

    return(spec_dict)



def spec_calc_osip_bounds(spec_dict, subset_sources, num_sources, fits_list_par, obsid_par, outdir, osip_frac_par):
    """
    Determines the OSIP (order sorting integrated probabilities) window (['osip_low'] and ['osip_high']) at the 
    location on the detector where confusion may have occured. CIAO will use the OSIP tables to determine a valid 
    range of energies (wavelength) to assign to each order based on the expected wavelength at the specific location 
    on the detector (along the grating arm). If a confusing source happens to disperse light at this same location then 
    all events within the OSIP range will be 'accepted' and thus confusion may have occured only within these bounds. 
    In practice, the OSIP wavelength range can be quite large and is only used as a first filter to determine if 
    confusion could occur. More strict confusion checking is done in spec_flag_set().

    Parameters
    ----------
    spec_dict : dictionary
        Spectral confusion dictionary which holds all possible spectral confusion entries for every source in main_list.
    subset_sources : int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    num_sources : int
        Number of sources in the main_list.
    fits_list_par : str
        evt2 file associated with the observation for the confusion determination.
    obsid_par : str
        obsID value of the observation.
    outdir : str
        Output directory used to create the log file assocaited with running the osip function.
    osip_frac_par : float
        CrissCross parameter which controls the size of the OSIP window. A value of 1.0 keep 100% of the OSIP window.
        This parameter can be tweaked lower to make the confusion estimate less conservative.
    """

    #remove non-order-specific keys for easy looping below.
    keys_list = list(spec_dict.keys())
    keys_list.remove('intersect_dist')
    keys_list.remove('xintercept')
    keys_list.remove('yintercept')
    keys_list.remove('flag')
    keys_list.remove('flag_comment')

    #call the OSIP only once per observation
    osip = OSIP(fits_list_par)

    spec_confuse_log_file = open(f'{outdir}/spec_confuse_{obsid_par}_log.txt', 'w')
    planck_time_c = (4.1357E-15 * 2.998E18) #conversion for E = hc/lamda where h and c are units of plancks const and angstrom/s
    
    for i in subset_sources:
        for j in range (num_sources):
            for m in keys_list:

                if 'heg' in m:
                    arm = 'heg'
                elif 'meg' in m:
                    arm = 'meg'
                else:
                    raise ValueError(f'Arm value not in spec_dict dictionary')

                if spec_dict[m]['wave'][i,j] != 0: #dont run for sources with no potential confusion
                    energy_low = []
                    energy_high = []
                    frac_osip = []
                    results = []

                    #calc osip for each subset source
                    results = osip(spec_dict['xintercept'][arm][i,j], spec_dict['yintercept'][arm][i,j], (planck_time_c/spec_dict[m]['wave'][i,j]), spec_confuse_log_file)

                    energy_low, energy_high, frac_resp = results
                    
                    #convert osip from energy to angstrom and account for user parameter osip_frac (fractional size of osip window of choice --e.g., user could want smaller than large osip window)
                    spec_dict[m]['osip_low'][i,j] = planck_time_c/energy_high + (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )
                    spec_dict[m]['osip_high'][i,j] = planck_time_c/energy_low - (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )	

    spec_confuse_log_file.close()
    return(spec_dict)



def spec_flag_set(spec_dict, src_pos_x_par, src_pos_y_par, subset_sources, fits_list_par, arf_ratios_dir_par, spec_confuse_limit_par, meg_cutoff_low, meg_cutoff_high, heg_cutoff_low, heg_cutoff_high):

    """
    This function sets the spec_conf[arm+order]['flag'][i,j] for spectral confusion (two arms intersecting). It runs
    spec_id_clean() to set the flags where confusion is impossible (i,j arms don't intersect) and spec_id_confuse() 
    to set flags for the remaining source pairs. This function only sets the dictionary values for spec_conf[arm+order]
    [i,j]['flag'] and ['flag_comment'] and returns the dictionary with these values updated based on confusion.
    Nomenclature: 'Confuser Source' is a source that contaminates another source's spectrum. 'Confused Source' is a 
    source whose spectrum is contaminated by another source.

    Parameters
    ----------
    spec_dict : dictionary
        Spectral confusion dictionary which holds all possible spectral confusion entries for every source in main_list.
    src_pos_x_par, src_pos_y_par : float
        Positions in physical units associated with sources in the main_list.
    subset_sources : int
        List of sources to create confusion tables for whose elements are matched to the main_list.
    fits_list_par : str
        evt2 file associciated with the observation
    arf_ratios_dir_par : str
        Path to CrissCross arf ratios tables necessary to account for efficiencies between orders.
    

    Spectral Confusion Flag Definitions
    -----------------------------------

    'clean' -- Source 'i' does not have any confusion from source 'j' in the arm/order listed.
    'warn' -- Source 'i' should not have any confusion from source 'j' in the arm/order listed. However, certain 
        confusion requirements were met but determined to not sufficiently cause confusion.
    'confused' -- Source 'i' is confused by source 'j' and the determined wavelength range should not be used for 
        spectral fitting without accounting for the confuser src 'j'.

    #Flag Numbers

    99 -- [CLEAN] i=j or spec_dict[m]['wave'][i,j] == 0 which indicates no confusion 
    980 -- [CONFUSED] Confused source has 0 dispersed counts and the confuser source has > 0 dispersed counts in 
        confuser order 
    981 -- [WARN] Confuser source has 0 dispersed counts in the appropriate wavelength range of confused source. 
    985 -- [WARN] both sources contribute dispersed counts in the region of interest but the ratio 
        (counts_confuser / counts_confused) is less than user specified 'spec_confuse_limit' par. 
    985 -- [CONFUSED] both sources contribute dispersed counts in the region of interest and the ratio 
        (counts_confuser / counts_confused) is greater than user specified 'spec_confuse_limit' par.
    992 -- [WARN] confuser source has appropriate geometry to contribute confusing counts but it's 0th order has 
        0 counts so no confusion 
    995 -- [WARN] confusion from confuser source has occured OUTSIDE the approrpriate range for the potentially 
        confused source (HEG/MEG cutoff OR OSIP_boundaries )
    996 -- [WARN] confuser from confuser source has occured OUTSIDE the approrpriate range for the confuser source 
        (HEG/MEG cutoff of confuser source)
    """

    #Calculate number of counts when determining CONFUSER counts in one order compared to CONFUSED counts in another order.
    def calc_num_counts(ratio_pycrates, order, order_zero_counts, bin_start, bin_end):

        """
        Estimates the number of Nth order counts in a spectral arm given a number of 0th order counts and a discrete 
        wavelength range. This information comes from the data table of ARF ratios (Nth_order / 0th_order) calculated 
        from a single HETG on-axis observation. This is to be used as an approximation and will not be exact. If the 
        discrete wavelength range covers several ARF bins then a mean of the spectral response bandpass is calculated. 
        Note, some bandpasses cover big dips in ARF and thus mean may affect results.

        Parameters
        ----------
        ratio_pycrates : fits table
            CrissCross fits input table which contains the ratios of responses based on a single on-axis HETG 
            observation. Note, since this takes the ratio of different orders, the buildup of ACIS contamination over
            time should not affect this calculation.
        order : crates column
            The crates column associated with HEG/MEG order.
        order_zero_counts : int
            The number of 0th order counts of the confused source determined in the wavelength bandpass where spectral 
            confusion occurs. This number will be calculated by counts_circle_band().
        bin_start, bin_end : float
            The first and last wavelength in Angstrom where mean response is taken in the ARF tables.

        Returns
        -------
        num_counts = An estimation of the number of counts from the confusing source expected to be dispersed into 
        the confused spectral order.
        avg_ratio_value = The average spectral response in the bin_start, bin_end bandpass used to estimate num_counts.
        """

        #this is to prevent issue where osip window might lie a little outside the window of the ARFs. This is not frequently triggered and when it is, its at an irrelevant wavelength range (e.g., 1 A)
        if bin_start < 1.0:
            #print(f'WARNING -- A response between {bin_start}:{bin_end} was requested for a source. The bin_start response was pegged to 1.0 A in calc_num_counts because it is less than minumum BIN.LO value in HEG/MEG arf ratio table.')
            bin_start = 1.0

        first_bin_index = np.where(ratio_pycrates.BIN_LO.values <= bin_start)[0][0] # since array is sorted IN bin, take the first index value that is true and 
        last_bin_index = np.where(ratio_pycrates.BIN_LO.values < bin_end)[0][0] # since array is sorted IN bin, take the first index value that is true and 
        order_data = ratio_pycrates.get_column(order)

        #if the bandpass only covers one bin then np.average wont work so need to check
        if first_bin_index != last_bin_index:
            avg_ratio_value = np.average(order_data.values[last_bin_index:first_bin_index])
        else:
            avg_ratio_value = order_data.values[first_bin_index] #assign it the response of the single bin if its only one bin wide

        num_counts = avg_ratio_value * order_zero_counts

        return(num_counts, avg_ratio_value)


    def spec_id_clean(spec_dict, num_sources, flag_clean, flag_99):
        """
        Identifies the obvious cases where spectra are 'clean' because their arms do not intersect with eachother. 
        Modifies spec_dict flag values appropriately and returns spec_dict. This function should always be run before 
        spec_id_confusion() because spec_id_confusion() acts on cleaned flag in logic.

        Parameters
        ----------
        spec_dict : dictionary
            Spectral confusion dict which holds all possible spectral confusion entries for every source in main_list.
        num_sources : int
            Number of sources in the main_list.
        flag_clean : str
            The text associated with a clean status
        flag_99 : str
            The text associataed with the flag_99 flag (spectral arns do not intersect).

        returns:
            spec_dict = the input spectral confusion dictionary with 'flag' and 'flag_comment' values updated 
            if their [i,j] arms do not intersect.
        """
        #need the keys AND the order numbers in string format
        keys_list = list(spec_dict.keys())
        keys_list.remove('intersect_dist')
        keys_list.remove('xintercept')
        keys_list.remove('yintercept')
        keys_list.remove('flag')
        keys_list.remove('flag_comment')

        #This loop sets the flags for when confusion DOES NOT occur. Consider changing in future where default flag value is 'no confusion' and I set when it DOES occur
        for i in range(0,num_sources):	#loop through each instance of spectral confusion for each source
            for j in range(0, num_sources):
                for m in keys_list: #one of the keys is 'intersect' so I can't loop through just keys. I need to make sure I'm just looking through the arms (which have subkeys wave and flag)
                
    #					if list(spec_dict[m].keys()) == ['wave', 'flag']: #5/3/24 -- note, I removed because I THINK this was older an no longer necessary.
                    if spec_dict[m]['wave'][i,j] == 0 or i == j:	#if the spec_conf[arm]['wave'][i,j] value is 0 or if i=j (cant have that confusion) then flag is set to 99 (no intersect)
                        #spec_dict[m]['flag'][i,j] = 99
                        spec_dict[m]['flag'][i,j] = flag_clean
                        spec_dict[m]['flag_comment'][i,j] = flag_99 # dont add on to previous comment cause if there is no intersection then this can be used in loop to only run confusion for intersecting sources


        return(spec_dict)


    def spec_id_confusion(spec_dict, subset_sources, arm_par, src_pos_x_par, src_pos_y_par):
        """
        Identifies cases of spectral confusion after obvious cases of no confusion are flagged as clean with 
        spec_id_clean(). This function runs for a single arm (heg/meg) at a time (primary) but the opposite 
        arm (secondary) is still used in calculations. 

        Parameters
        ----------
        spec_dict : dictionary
            Spectral confusion dict which holds all possible spectral confusion entries for every source in main_list.
        subset_sources : int
            List of sources to create confusion tables for whose elements are matched to the main_list.
        arm_par : str
            HETG arm parameter 'heg' or 'meg'.
        src_pos_x_par, src_pos_y_par : float
            Positions in physical units associated with sources in the main_list.    

        Returns
        -------
        spec_dict = the input spectral confusion dictionary with 'flag' and 'flag_comment' values updated for confusion

        Notes
        -----
        
        The logic in this function is complicated so it is summarized here:

        (1) Run the following checks only for the cases where spectral arms intersect and then set flag appropriately:

        (a) If the confuser source intersects the arm of the (potentially) confused source outside of the heg/meg 
            cutoff energies (<1 A or >~ 16, 32 A) of the confused source then NO ORDERS of the confuser source could 
            confuse so assign a warning flag (flag_995) 

        (b) If the intersection occurs in the valid range of wavelengths for meg/heg then check the following for 
            EACH order:
            
            (i) Is the confuser's m order wavelength range within the bounds of HEG/MEG? If not, set warning flag 
                (flag_996) and check other orders.
            
            (ii) If (i) is TRUE, is the confuser's m order within the same wavelength range as the confused source is 
                expecting at the location of the intersection (i.e., the OSIP window of the confused source at the 
                intersection location)? If not, mark as 'clean' unless a previous order has been flagged as 'warn' 
                or 'confused'.
            
            (iii) If (ii) is TRUE then calculate the number of 0th order counts of the CONFUSER source within the OSIP 
            range for the spectral intersection location. If confuser source 0th order has 0 counts then no need to 
            check for confusion anymore and set 'warning' flag. If confuser 0th order has > 0 counts then determine 
            the number of 0th order counts from the CONFUSED source in the OSIP range. Use the number of 0th order 
            counts for both sources and the HEG/MEG-0th-order-to-nth-order ARF tables to estimate the number of 
            dispersed counts from both sources landing in the intersection spot of the potentially confused source. 
            Use ratio of estimated dispersed counts to determine if confusion occurs and flag appropriately. 
            
        This calculation should account for the heg/meg order efficiencies and ARFs BUT assumes an on-axis source at 
        the pointing location. This WILL be slightly different for any other source but to first order it should be ok.
        This calculation uses the AVERAGE response ratio in the calculated OSIP range. If OSIP range is large then 
        it is washing out some details in the arfs but for estimation purposes it should be ok.
        """

        #call these once per observation and used in counts_circle_band function
        skyconverter = Sky2Chandra(fits_list_par)
        evtcrates = read_file(fits_list_par)

        #set the primary arm so the opposite arm is then the secondary
        primary_arm = arm_par

        if arm_par == 'heg':
            #load the arf ratio table data
            primary_arf = read_file(f'{arf_ratios_dir_par}/HEG_Nth_0th_order_ratios_mkarf.fits')
            arm_cutoff_low = heg_cutoff_low
            arm_cutoff_high = heg_cutoff_high
            secondary_arm = 'meg'
            secondary_arf=  read_file(f'{arf_ratios_dir_par}/MEG_Nth_0th_order_ratios_mkarf.fits')

        elif arm_par == 'meg':
            primary_arf = read_file(f'{arf_ratios_dir_par}/MEG_Nth_0th_order_ratios_mkarf.fits')
            arm_cutoff_low = meg_cutoff_low
            arm_cutoff_high = meg_cutoff_high
            secondary_arm = 'heg'
            secondary_arf=  read_file(f'{arf_ratios_dir_par}/HEG_Nth_0th_order_ratios_mkarf.fits')

        else:
            raise ValueError('arm_par not "heg" or "meg" ') 

        #for each primary arm, determine if confusion can/has occured and set the appropriate flags and flag_comments.
        for i in subset_sources:
            for j in range(0,len(src_pos_x_par)):
                for n in ['-3','-2','-1','+1','+2','+3']:

                    if (spec_dict[primary_arm+n]['flag_comment'][i,j] != flag_99): #dont run counts_circle_band unless there is at least some evidence of confusion - note I am leaving of 999 here cause there could be a case of confusion near the edges where the osip range brings into the real band

                        #if the region in the extracted spectrum where confusion occurs is outside the valid wavelength range then flag as warning and continue

                        ##KEEP THIS COMMENT--> First check if the intersection between two spectra occur in the possible range of wavelengths for the extracted spectra. If not, it doesn't matter what order or wavelength the other source is, it will NEVER contribute to confusion cause effective area will zero out any flux outside valid range of wave for each source.
                        if spec_dict[primary_arm+n]['wave'][i,j] < (arm_cutoff_low) or spec_dict[primary_arm+n]['wave'][i,j] > (arm_cutoff_high):
                        #if spec_dict[primary_arm+n]['wave'][i,j] < (arm_cutoff_low/np.abs(int(n))) or spec_dict[primary_arm+n]['wave'][i,j] > (arm_cutoff_high/np.abs(int(n))):
                            spec_dict[primary_arm+n]['flag'][i,j] = flag_warn
                            spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_995

                        #if the intersection occurs within the valid bounds of the extracted source then check all the orders of the confusing source to see if those are within THEIR respective valid bounds. If they are outside their own bounds then confusion will not occur
                        else:

                            #set these to NONE HERE so they aren't recalculated needlessly for each confuser order
                            confused_0th_counts = [None]
                            confuser_0th_counts = [None]
                            
                            #otherwise (confusion occurs within extracted wavelength range) so check all the orders to see if their contaminating photons occur outside of their respective valid wavelength ranges
                            #for m in [1,2,3]:
                            #AT this point we know heg and meg arm intersect somewhere within the valid range of the confused (heg) arm. Now we check the valid range of the confuser and if that is valid then do the calculation to see how many spectral counts confuse
                            for m in ['-3','-2','-1','+1','+2','+3']:
                                #CHECK IF INTERSECTION OCCURS OUTSIDE NORMAL WAVELENGTH BOUNDS FOR HEG --> only one of these can be triggered cause only one +/- arm will intersect. HEG/MEG cutoff should not depend on order cause I am checking within the reference frame of the confuser source. 

                                if spec_dict[secondary_arm+m]['wave'][j,i] != 0 and (spec_dict[secondary_arm+m]['wave'][j,i] < (arm_cutoff_low) or spec_dict[secondary_arm+m]['wave'][j,i] > (arm_cutoff_high)):
                                    if spec_dict[primary_arm+n]['flag'][i,j] != flag_confused:
                                        spec_dict[primary_arm+n]['flag'][i,j] = flag_warn
                                    spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] +  flag_996
                                
                                #if none of the flag_995s trigger that means spectral confusion has occured within the valid ranges of wavelengths and we need to check counts
                                else:

                                    #START OSIP DETERMINATION FOR EVERY SOURCE with some intersection

                                    #if CONFUSER source has photons with wavelengths within the OSIP region of the CONFUSED source then run counts_circle_band to determine if confusion can occur. If so, flag. Otherwise, that means there was a potential source of confusion but it was outside OSIP range so it can get a flag of clean if no other orders cause issues. 
                                    #I was worried if osip_low == 0 then the WRONG arm where no confusion occurs would have its wave[j,i] = 0 and trigger this incorrectly. However 0 is not greater than 0 so just dont change to '>=' and it should be ok.
                                    
                                    #if the photons that land in the confused region are within the OSIP bounds then check the number of counts compared to the source counts in that region
                                    if (spec_dict[secondary_arm+m]['wave'][j,i] > spec_dict[primary_arm+n]['osip_low'][i,j] and spec_dict[secondary_arm+m]['wave'][j,i] < spec_dict[primary_arm+n]['osip_high'][i,j]):

                                        #only run counts_circle_band ONCE per M order cause the 0th order counts dont change
                                        #run confuser counts first cause if no counts here then all the future calculations are pointless cause no confusion.
                                        if confuser_0th_counts == [None]:
                                            confuser_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[j], src_pos_y_par[j], [spec_dict[primary_arm+n]['osip_low'][i,j],spec_dict[primary_arm+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in contaminating spectrum at SAME osip window  of confusion

                                        #if confuser_0th_counts = 0 then we can stop checking the other m orders of the confuser source cause its always the same osip window and if there are no counts in that osip window in the 0th order of the confuser then there wont be confusion in the confused order (ADVANCE n if confuser_0th_counts = 0). It's ok to keep specific m flags cause it will provide knowledge of which m orders had the appropriate osip range.
                                        if confuser_0th_counts == 0: #could make this number '< 3 or so' if I want to reduce the number of false positives and allow some more cases through to be OK. see code comment above
                                                
                                            spec_dict[primary_arm+n]['flag'][i,j] = flag_warn #confuser has appropriate geometry to contribute confusing counts but it's 0th order has 0 counts	so no confusion				
                                            spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_992 + m

                                        #if confuser counts !=0 then I need to run the calculation to determine if dispersed events land in region
                                        else:
                                        
                                            #only run counts_circle_band ONCE per M order cause the 0th order counts dont change
                                            if confused_0th_counts == [None]:
                                                confused_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[i], src_pos_y_par[i], [spec_dict[primary_arm+n]['osip_low'][i,j],spec_dict[primary_arm+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in the spectrum of interest at osip window of confusion 											

                                        #if (confuser_counts > 0 and confused_counts > 0):

                                            #for negative orders mult by -1 so the string is positive. This needs to match HEG/MEG arf table in primary/secondary_arf 
                                            if int(n) > 0:
                                                primary_order = f'p{int(n)}_to_0'
                                            elif int(n) < 0:
                                                primary_order = f'm{-1*int(n)}_to_0'
                                            else:
                                                raise ValueError('Cannot set primary_order variable for ARF ratios')

                                            if int(m) > 0:
                                                secondary_order = f'p{int(m)}_to_0'
                                            elif int(m) < 0:
                                                secondary_order = f'm{-1*int(m)}_to_0'
                                            else:
                                                raise ValueError('Cannot set secondary_order variable for ARF ratios')
                                                
                                            
                                            #The estimated number of dispersed counts from the primary (confused) source at the location of the spectral intersection (confusion)
                                            confused_counts_primary = []
                                            confused_counts_primary, avg_ratio_primary = calc_num_counts(ratio_pycrates = primary_arf, order = primary_order, order_zero_counts =confused_0th_counts, bin_start=spec_dict[primary_arm+n]['osip_low'][i,j], bin_end = spec_dict[primary_arm+n]['osip_high'][i,j])

                                            #The estimated number of dispersed counts from the secondary (confuser) source at the location of the spectral intersection (confusion)
                                            confuser_counts_secondary = []
                                            confuser_counts_secondary, avg_ratio_secondary = calc_num_counts(ratio_pycrates = secondary_arf, order = secondary_order, order_zero_counts =confuser_0th_counts, bin_start=spec_dict[primary_arm+n]['osip_low'][i,j], bin_end = spec_dict[primary_arm+n]['osip_high'][i,j])

                                            if (confuser_counts_secondary > 0 and confused_counts_primary == 0):
                                                spec_dict[primary_arm+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
                                                spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_980 + m
                                            
                                            elif (confuser_counts_secondary == 0):
                                                #DONT OVERWRITE FLAG ONCE IT GETS SET TO CONFUSED
                                                if spec_dict[primary_arm+n]['flag'][i,j] != flag_confused:
                                                    spec_dict[primary_arm+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 
                                                
                                                spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_981 + m


                                            elif (confuser_counts_secondary > 0 and confused_counts_primary >0):

                                                spec_confused_ratio = []
                                                spec_confused_ratio = (confuser_counts_secondary / confused_counts_primary)

                                                #if the ratio of confusing counts / confused sources counts is higher than some user param then flag as confused
                                                if spec_confused_ratio > spec_confuse_limit_par:
                                                    spec_dict[primary_arm+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
                                                    spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_986 + m													
                                                else:
                                                    if spec_dict[primary_arm+n]['flag'][i,j] != flag_confused:
                                                        spec_dict[primary_arm+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 

                                                    #add warning showing that there is confusion but its lower than some threshold so its ok.
                                                    spec_dict[primary_arm+n]['flag_comment'][i,j] = spec_dict[primary_arm+n]['flag_comment'][i,j] + flag_985 + m
                                                    
                                            else:
                                                print(f'ERROR --> Something went wrong when determining spectral confusion HEG. i={i},j={j},n={n},m={m}, confused_cnt_{primary_arm}={confused_counts_primary}, confuser_cnt_{secondary_arm}={confuser_counts_secondary}, 0th_ord={confused_0th_counts, confuser_0th_counts}')
                                                print()

                                    #dont overwrite 999 but if the source is otherwise outside the OSIP range then its flag is changed to 995. Sources with 999 that ARE within the osip range will have their 999 change in above loop conditions.
                                    #ASSUMING FLAG WAS PREVIOUSLY 'unset' then mark it as clean if it didn't land in the above loops
                                    elif spec_dict[primary_arm+n]['flag'][i,j] != flag_warn and spec_dict[primary_arm+n]['flag'][i,j] != flag_confused:
                                        spec_dict[primary_arm+n]['flag'][i,j] = flag_clean #If it doesnt makes it through the top loop condition then confusion is outside OSIP bounds and should be clean. If it already has A warning or confusion flag then it remains confused and set.
                                    #else: no need for else statement to catch remainder of cases because if it is already marked as confused or warn it should STAY confused or warned

        return(spec_dict)



    ###FLAG DEFINITIONS####
    flag_clean = 'clean'
    flag_warn = 'warn'
    flag_confused = 'confused'

    #text to add to ['flag_comment'] if triggered. Leading commas are intentional.
    flag_99 = 'no_intersect,'
    flag_995 = ',outside_primary_source_wave_coverage'
    flag_996 = ',outside_confuser_source_wave_coverage'
    flag_992 = ',confuser_has_no_0th_order_counts_triggered_by_order_'
    flag_980 = ',confused_has_0_disp_counts_and_confuser_gtr_0_by_order_'
    flag_981 = ',confuser_has_0_disp_counts_in_order_'
    flag_985 = ',confusion_smaller_than_conf_ratio_by_order_'
    flag_986 = ',confusion_above_conf_ratio_by_order_'

    #######################


    #Flag the unconfused (clean) spectra as clean. This must be run before spec_id_confusion().
    spec_dict = spec_id_clean(spec_dict=spec_dict, num_sources=len(src_pos_x_par), flag_clean=flag_clean, flag_99=flag_99)
                
    #Identify where confusion can occur and flag appropriately. This must be run AFTER spec_id_clean()
    spec_dict = spec_id_confusion(spec_dict=spec_dict, subset_sources=subset_sources, arm_par='heg', src_pos_x_par = src_pos_x_par, src_pos_y_par = src_pos_y_par)
    spec_dict = spec_id_confusion(spec_dict=spec_dict, subset_sources=subset_sources, arm_par='meg', src_pos_x_par = src_pos_x_par, src_pos_y_par = src_pos_y_par)


    return(spec_dict)




####POINT SOURCE CONFUSION FUNCTIONS####


def pntsrc_dist_to_spec(pntsrc_dict, src_pos_x_par, src_pos_y_par, xoff_par, yoff_par, m_arm_par, b_arm_par, arm_ang_par, arm_par):
    """
    Calculates 'perp_dist_to_spec' which is the distance in pixels between a confusing 0th order point 
    source and the dipersed spectrum of the confused source (measured perpendicular to the spectrum). It also calculates 
    ['intersect_dist'][arm_par][i,j] variable which is the distance from the 0th order to the 0th order confuser along 
    the grating arm. NOTE: This calculation should be valid regardless of the roll angle. However, roll angle is used 
    in other functions to determine which orders to fill based on whether 0th order source is 'above' or 'below' the 
    potentially confused grating arm in detector coordinates.

    Parameters
    ----------
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.    
    src_pos_x_par, src_pos_y_par : float
        Positions in physical units associated with sources in the main_list.
    xoff_par, yoff_pa : int
        X and Y offset values necessary to ensure equation of line intersection parameters all stay positive.
    m_arm_par : float
        Slope of the grating line on the detector (from y=mx+b and the grating instrumental slope).
    b_arm_par : float
        HEG/MEG line intercept value (from y=mx+b).
    arm_ang_par : float
        Instrumental grating arm HEG/MEG angle that vary relative to roll angle.
    arm_par : str
        HETG 'heg' or 'meg' arm.

    Returns
    -------
    pntsrc_dict : updates the pntsrc_dict parameters and returns them.
    perp_dist_to_spec_arm : perpendicular distance to spectral arm for every i,j pair.
    r0_offset_dist_from_contam_arm : a necessary value when calculating the wavelength where pntsrc confusion occurs.
    """

    ###Identify point sources that fall on the lines of other sources dispersed spectra
    # plug in the X coord of all sources into the equation of a line and if the y coord of that source is +/- contam_offset_par(see below) from the y after plugging in x then it is on or near the line.

    #initialize values
    yintercept_pointsrc_arm=np.zeros((len(src_pos_x_par),len(src_pos_x_par))) #y intercept value
    
    ydistance_to_spectrum_arm=np.zeros((len(src_pos_x_par),len(src_pos_x_par))) #this is what the value of Y (j) should be if X (j) is on the line (i). In other words, the y value of j where it intersects the dispersed spectrum if drawn directly down.   yintercept_pointsrc is what the Y value of the contaminating source SHOULD BE if it fell EXACTLY on the line of a different source.  Note that Y does not equal distance to disperssed spectrum. The y distance above the dispersed spectrum is just src_pos_y[j] - yintercept_pointsrc[i,j]

    perp_dist_to_spec_arm=np.zeros((len(src_pos_x_par),len(src_pos_x_par))) #this is the perpendicular distance (or the shortest distance from contaminating source to the dispersed spectrum).  

    r0_offset_dist_from_contam_arm=np.zeros((len(src_pos_x_par),len(src_pos_x_par))) #This par is hard to explain.  If you draw a line in the y direction from the contaminating point source to the dispersed spectrum you get endpoint #1. If you draw a line from the contaminating point source DIRECTLY (shortest distance, perpendicular) to the dispersed spectrum, you get endpoint #2.  This parameter is the distance difference between these two endpoints.  This is to calculate the distance from endpoint#1 to the zeroth order and then ADD to that this offset distance to get the final distance (location in the dispersed specturm) where the contaminating source would influence its spectrum. 
    
    #first calculate perp_dist_to_spec_arm
    for i in range (len(src_pos_x_par)):
        for j in range (len(src_pos_x_par)):
            yintercept_pointsrc_arm[i,j] = yoff_par + ((m_arm_par*(src_pos_x_par[j]-xoff_par))+b_arm_par[i]) #NOTE-- Would this be easier to calculate as tan(arm_ang_par) * (abs(src_pos_x[j] - src_pos_x[i]))? Seems way less complicated and shouldn't depend on roll
            ydistance_to_spectrum_arm[i,j] = src_pos_y_par[j] - yintercept_pointsrc_arm[i,j] 
            perp_dist_to_spec_arm[i,j] = ydistance_to_spectrum_arm[i,j] * math.sin(math.radians(90 - arm_ang_par)) 
            r0_offset_dist_from_contam_arm[i,j]  = ydistance_to_spectrum_arm[i,j] * math.cos(math.radians(90 - arm_ang_par)) 
            
            #to be consistent with previous code, only calculate if this value != 0. Might be able to remove this condition later
            if perp_dist_to_spec_arm[i,j] != 0:
                pntsrc_dict['intersect_dist'][arm_par][i,j] = abs((src_pos_x_par[j]-src_pos_x_par[i]) / math.sin(math.radians(90-arm_ang_par)) + r0_offset_dist_from_contam_arm[i,j])

    return(pntsrc_dict, perp_dist_to_spec_arm, r0_offset_dist_from_contam_arm)




def pntsrc_confuse_wave(pntsrc_dict, perp_dist_to_spec_arm_par, src_pos_x_par, P_arm_par, mm_per_pix, X_R, arm_par, roll_nom_par, src_off_axis_par, counts_par, max_pntsrc_dist_par, min_spec_counts_par, min_pntsrc_counts_par):

    """
    Identifies when point source confusion occurs within the thresholds provided by the user. If a 0th order source is 
    sufficiently bright and close to the dispersed spectrum of another source then it will be identified as having 
    point source confusion.  This function uses output from pntsrc_dist_to_spec() with the roll angle to determine 
    where/if point source confusion occurs. NOTE: a single confusing point source can only confuse a single arm for 
    each 'confused' source. So this loop will only flag a single arm for each confused source per confuser source.

    Parameters
    ----------
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.    
    perp_dist_to_spec_arm_par : float
        Perpendicular distance to spectral arm for every i,j pair. Each arm heg/meg will have its own perp_dist_to_spec
        parameter which is why function require arm_par.
    src_pos_x_par, src_pos_y_par : float
        Positions in physical units associated with sources in the main_list.
    P_arm_par : float
        HEG or MEG gratings period which is an instrumental constant.
    mm_per_pix : float
        The constant number of millimeters per ACIS pixel. (CONSTANT = 0.023987)
    X_R : float
        Rowland  diameter in millimeters (CONSTANT=8632.48)
    arm_par : str
        HETG 'heg' or 'meg' arm.
    roll_nom_Par : float
        Roll angle of the observation taken from the fits header.
    src_off_axis_par : float
        Off-axis angle of the source in arcseconds
    counts_par : int
        The number of 0th order counts.
    max_pntsrc_dist_par : int
        CrissCross parameter threshold in number of pixels for how far a point source can be perpendicular to a 
        disperssed spectrum before it is no longer considered in the confusion calculation. This number can be increased
        to reduce the number of potentially confusing point sources.
    min_spec_counts_par : int
        CrissCross parameter threshold in counts above which a confused source is considered bright enough for point 
        source confusion estimation.
    min_pntsrc_counts_par : int
        CrissCross parameter threshold in counts above which a 0th order source is bright enough to be 
        considered as a confuser source of another source's spectrum.
    """

    #note, the wavelength calculation here depends on the roll angle of the observation only because determination of the order (e.g., -1 versus +1) depends on roll angle in functions above (see intersect_dist and r0_offset_dist)
    for i in range (len(src_pos_x_par)):
        for j in range (len(src_pos_x_par)):

            if src_off_axis_par[j] <= 180:
                off_axis_modifier = 1
            elif (src_off_axis_par[j] > 180 and src_off_axis_par[j] < 360):
                off_axis_modifier = 2
            elif src_off_axis_par[j] >= 360:
                off_axis_modifier = 3
            else:
                print('ERROR off axis check')				

            if i != j and perp_dist_to_spec_arm_par[i,j] !=0 and (abs(perp_dist_to_spec_arm_par[i,j]) < (max_pntsrc_dist_par * off_axis_modifier)) and counts_par[i] > min_spec_counts_par and counts_par[j] > min_pntsrc_counts_par:
                for m in ['1','2','3']:
                    if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
                        if src_pos_x_par[j] > src_pos_x_par[i]:
                            pntsrc_dict[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_dict['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number
                        elif src_pos_x_par[j] < src_pos_x_par[i]:
                            pntsrc_dict[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_dict['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number		
                        else:
                            print(f'ERROR in point source confuse calculation for i,j,m = {i,j,m}')													
                    elif (roll_nom_par > 90 and roll_nom_par < 270):
                        if src_pos_x_par[j] < src_pos_x_par[i]:
                            pntsrc_dict[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_dict['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number
                        elif src_pos_x_par[j] > src_pos_x_par[i]:
                            pntsrc_dict[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_dict['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number							
                        else:
                            print(f'ERROR in point source confuse calculation for i,j,m, roll_nom_par = {i,j,m, roll_nom_par}')
                    else:
                        print('ERROR -- Check roll_nom_par value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')		

    return(pntsrc_dict)
                        



def pntsrc_confuse_wave_bounds(pntsrc_dict, perp_dist_to_spec_arm_par, fits_list_par, subset_sources, src_pos_x_par, src_pos_y_par, arm_par,logfile_par, evt_frac_thresh=0.1):
    """
    This function will run pnt_src_masking_region() to determine if the PSF from a potentially confusing point source 
    is sufficient to actually cause confusion. It uses pnt_src_masking_region() which provides a wavelength RANGE to 
    ignore for each spectrum based on the PSF size and energy of the confusing source. pnt_src_masking_region uses the 
    total number of 0th order counts in the contaminating source and identifies a radius in that source's PSF 
    (which is on the grating arm) where GREATER than that radius, the effect of the contaminating counts is 
    insignificant. For example, the PSF has most counts near its center so at some radius the counts fraction will 
    become much smaller than near the center and can be ignored.  This 'radius' is along the grating arm but 
    corresponds to the size of the confusing 0th orders source's PSF. This is why the ignore regions for the point 
    sources are so much smaller than the spectral arm OSIP crosses. The PSF can be modeled and easily understood as 
    a fraction of the stars counts. Arm crossings are not as easy. So in essence, this boundary is NOT the OSIP range. 
    So the LOW is the lower bound and the high is the upper bound. If the value returned is 9999.0 then that is a flag 
    which indicates the point source does not have any counts in the expected band (and thus isn't confusing the 
    spectrum). 

    Parameters
    ----------
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.    
    perp_dist_to_spec_arm_par : float
        Perpendicular distance to spectral arm for every i,j pair. Each arm heg/meg will have its own perp_dist_to_spec
        parameter which is why function require arm_par.
    fits_list_par : str
        evt2 file for confusion calculation
    subset_sources : str
        list of sources to generate confusion files for.
    src_pos_x_par, src_pos_y_par : float
        Positions in physical units associated with sources in the main_list.
    arm_par : str
        HETG 'heg' or 'meg' arm. 
    logfile_par : str
        Name of the logfile for capturing pnt_src_masking_region() log output.
    evt_frac_thresh : float
        Fraction of events allowed by confuser before considering confusion occurs (0.1 = 10%)

    Returns
    -------
    pntsrc_dict : updates values in the pnsrc_confusion dictionary and returns the dictionary.
    """

    if arm_par == 'heg':
        tg_part = 1
    elif arm_par == 'meg':
        tg_part = 2
    else:
        raise ValueError('Cannot identify tg_part value from arm_par')
    
    osip = OSIP(fits_list_par)
    skyconverter = Sky2Chandra(fits_list_par)
    evtcrates = read_file(fits_list_par)

    pntsrc_confuse_log_file = open(f'{logfile_par}', 'w')

    for i in subset_sources:
        for j in range(0,len(src_pos_x_par)):
            for m in ['-3','-2','-1','+1','+2','+3']:
                if pntsrc_dict[arm_par+m]['wave'][i,j] != 0: #only calculate for potential sources of confusion
                    pntsrc_dict[arm_par+m]['wave_low'][i,j], pntsrc_dict[arm_par+m]['wave_high'][i,j] = pnt_src_masking_region( evtcrates, osip, skyconverter, src_pos_x_par[i], src_pos_y_par[i], src_pos_x_par[j], src_pos_y_par[j], np.abs(perp_dist_to_spec_arm_par[i,j]), pntsrc_dict[arm_par+m]['wave'][i,j], tg_part, evt_frac_thresh, pntsrc_confuse_log_file)

    pntsrc_confuse_log_file.close()

    return(pntsrc_dict)





def pntsrc_flag_set(pntsrc_dict, num_sources, arm_par, subset_sources, heg_cutoff_low_par, heg_cutoff_high_par, meg_cutoff_low_par, meg_cutoff_high_par):

    """
    Sets the various flags for point source confusion. Note, some flag values already stored in pntsrc_dict['wave'] 
    and ['wave_low']. These are passed to pntsrc_dict when running pntsrc_confuse_wave_bounds() so that is where some 
    confusion is actually determined. This function sets the  main arm/order flags.

    Parameters
    ----------
    pntsrc_dict : dictionary
        Point source confusion dict which holds all possible pntsrc confusion entries for every source in main_list.    
    subset_sources : str
        list of sources to generate confusion files for.
    src_pos_x_par, src_pos_y_par : float
        Positions in physical units associated with sources in the main_list.
    arm_par : str
        HETG 'heg' or 'meg' arm. 
    heg/meg cutoff low/high : float
        Wavelength in angstroms where the HEG and MEG effective areas go to zero or the user doesn't care outside those
        wavelength bounds. Any confusion that occurs outside these bounds is not marked as confused.
    
    Pntsrc Confusion Flag Def
    -------------------------
    flag_9999 -- [CLEAN] The 0th order confusing point source has 0 counts.
    flag_9998 -- [WARN] The 0th order confusing point source has too few counts to warrant confusion 
        (0th_order_counts_confuser / 0th_order_counts_confused) < 'factor' (~10% default).
    flag_9997 -- [WARN] The 0th order confusing point source is relatively weak and too far from spectrum to cause 
        confusion.
    flag_9995 -- [WARN] The 0th order confusing point source falls outside the valid range of HEG/MEG response bounds.
    flag_9996 -- [CONFUSED] The 0ther order confusing point source is valid and causes confusion.

    Note: if the confused spectrum has 0 counts then the entire OSIP range is used for ignoring point source confusion. 
    Otherwise, it is calculated based on fraction of PSF and brightness of confuser source.
    """

    flag_clean = 'clean'
    flag_warn = 'warn'
    flag_confused = 'confused'

    #text to add to flag_comments when triggered
    flag_9999 = 'confusing_pntsrc_but_no_counts'
    flag_9998 = 'confusing_pntsrc_but_relatively_few_counts'
    flag_9997 = 'confusing_pntsrc_too_weak_and_too_far'
    flag_9996 = 'pntsrc_confusion'
    flag_9995 = 'pntsrc_conf_outside_resp_region'

    if arm_par == 'heg':
        cutoff_low = heg_cutoff_low_par
        cutoff_high = heg_cutoff_high_par
    elif arm_par == 'meg':
        cutoff_low = meg_cutoff_low_par
        cutoff_high = meg_cutoff_high_par
    else:
        raise ValueError(' WRONG ARM PAR USED IN pntsrc_flag_set')

    for i in subset_sources:
        for j in range(0,num_sources):
            for m in ['-3','-2','-1','+1','+2','+3']:

                if pntsrc_dict[arm_par+m]['wave'][i,j] == 0:
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_clean

                elif pntsrc_dict[arm_par+m]['wave_low'][i,j] == 9999.0:
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_warn
                    pntsrc_dict[arm_par+m]['flag_comment'][i,j] = flag_9999

                elif (pntsrc_dict[arm_par+m]['wave'][i,j] < cutoff_low or pntsrc_dict[arm_par+m]['wave'][i,j] > cutoff_high):
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_warn
                    pntsrc_dict[arm_par+m]['flag_comment'][i,j] = flag_9995

                elif pntsrc_dict[arm_par+m]['wave_low'][i,j] == 9998.0:
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_warn
                    pntsrc_dict[arm_par+m]['flag_comment'][i,j] = flag_9998

                elif pntsrc_dict[arm_par+m]['wave_low'][i,j] == 9997.0:
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_warn
                    pntsrc_dict[arm_par+m]['flag_comment'][i,j] = flag_9997

                else:
                    pntsrc_dict[arm_par+m]['flag'][i,j] = flag_confused
                    pntsrc_dict[arm_par+m]['flag_comment'][i,j] = flag_9996				
                


    return(pntsrc_dict)




####ARM CONFUSION FUNCTIONS####

def arm_conf_dict(num_sources, highest_order):

    """
    A nested dictionary that holds all of the relevant data for confusion between two sources for all sources in the
    main_list. Each MEG/HEG arm has 6 orders and, in a general sense, all orders from one arm can interact with all 
    orders from another arm. This nested dictionary was created to intelligently hold all of this information while 
    still being relatively readable. The format of this dictionary is: arm_dict['arm+order'][parameter][i,j]
    where 'i' is the potentially CONFUSED source and 'j' is the potential CONFUSER source. This dictionary
    is slightly different than conf_dict() used for spectral and point source confusion. 
    
    Arm confusion occurs when a confuser source 'j' is bright enough to disperse many counts and lies on the arm of 
    another source bright enough to disperse many counts. 
    
    arm values : HETG arm values 'heg' or 'meg'        
    arm orders : HETG order values -3, -2, -1, +1, +2, +3  

    ['intersect_dist'] : The distance in pixels between the 0th order src 'i' and the 0th order src 'j' position along 
        the arm.
    ['0th_cnts_frac'] : the ratio of 0th order counts of the CONFUSER 'i' divided by CONFUSED 'j'
    ['arm_confused_wave'] : This identifies which order (e.g., -1 versus +1) the arm confusing 0th order point source 
        falls on. This is used when determinig the range of wavelengths confused in arm confusion.
    
    ['flag'] : primary flag which represents potential sources of confusion for ALL orders between source i and j.
    ['flag_comment'] : primary flag description which represents potential sources of confusion for ALL orders between 
        source i and j.

    ['arm+order']['wave'] : the wavelength where confusion may occur
    ['arm+order']['wave_low'] : the lower bounds of where confusion may occur
    ['arm+order']['wave_high'] : the upper bounds of where confusion may occur
    ['arm+order']['flag'] : the flag which represents potential sources of confusion for a paritcular order between 
        source i and j.
    ['arm+order']['flag_comment'] : the flag description which represents potential sources of confusion for a 
        paritcular order between source i and j.		

    """

    arms = ['heg', 'meg'] #arms will always be heg or meg
    arm_order = list() #create an empty list that gets appended with the arm+order

    order_arr = np.arange((-1 * highest_order), (highest_order+1)) #take the input highest order and make an array from (-highest_order to highest_order). Note, arange stops one early so must have +1
    order_list = list(order_arr) #convert the array to a list 
    order_list.remove(0) #remove '0' from the list 

    orders = list()

    for i in order_list:
        if i < 0:
            orders.append(str(i))
        if i > 0:
            orders.append('+'+str(i))

    for i in arms:
        for j in orders:
            arm_order.append(i+j) #combines the arm name and the order number to generate each dictionary key
    
    confusion_dict = {} #create an empty dictionary

    #for each arm+order, create empty arrays for wavelength and for flag		
    for k in arm_order:
        #confusion_dict[k] = np.zeros((num_sources,num_sources)) #this was the older way of doing it. DELETE when fair to do so
        confusion_dict[k] = {'wave': np.zeros((num_sources,num_sources)), 'wave_low': np.zeros((num_sources,num_sources)), 'wave_high': np.zeros((num_sources,num_sources)),  'flag': np.full((num_sources,num_sources), 'unset', dtype=object), 'flag_comment': np.full((num_sources,num_sources), '', dtype=object)}

    #add intersection_distance for each arm **NOTE-- this does NOT depend on order therefore it gets its own dict reference here and its not embedded in the arm loop.
    confusion_dict['intersect_dist'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))}

    confusion_dict['0th_cnts_frac'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))}

    confusion_dict['arm_confused_wave'] = {'heg': np.zeros((num_sources,num_sources)), 'meg': np.zeros((num_sources,num_sources))}

    #add main flag par - one that summarizes all arms to quickly identify if the extract source [i] has any confusion at all with another source [j]
    confusion_dict['flag'] = np.full((num_sources,num_sources), 'unset', dtype=object)
    confusion_dict['flag_comment'] = np.full((num_sources,num_sources), '', dtype=object)		
    
    return(confusion_dict)



def arm_confuse_wave(arm_dict, perp_dist_to_spec_arm_par, src_pos_x_par, P_arm_par, arm_par, arm_ang_par, roll_nom_par, src_off_axis_par, r0_offset_dist_from_contam_arm_par, counts_par, subset_sources, mm_per_pix_par, X_R_par, min_arm_counts, max_arm_dist):
    
    """
    Calculates ratio of 0th order counts (net_counts_confuser / net_counts_confused) for sources with potential 
    arm confusion. This parameter is used in loop logic to flag arm confusion but also printed to final table to 
    allow user's judgement in determining if they want to remove associated confusion or not.  Also calculates the 
    distance from the 0th order confused source (wavelength) where the 0th order of the confuser falls 
    on the spectrum. This distance (dx) is then used in later calculations to determine the wavelenght bounds where 
    arm confusion can occur.

    Notes
    -----
    Arm confusion is calculated using an off_axis_modifier which is an ESTIMATE of how the off-axis angle of 
    the confuser source may impact arm confusion due to its larger PSF size. This is separated into three spatial bins 
    of [< 3' (arcmin)], [> 3' and < 6'] and [> 6'] using Fig 4.13 of the Chandra proposers observing guide which shows 
    the HRMA encircled energy fraction for off-axis sources. Focusing on the 1.5 keV curve,  if a 1'' PSF is 2pix up and 
    2pix down (4pix but confusing source also has 4pix so equals 8pix then + 2 just in case = 10 = 
    max_arm_dist) then I can *assume* the number of pixels = 4*the eef. So at 2'' its off axis angle of 
    4' so then its 4pix*2+2 * 2 and so on and so on. Should be ok cause most sources at least [i] will be < 3' but 
    there may be issues for far off-axis sources espcially if they also intersect with other far off-axis sources.     

    Many of the arm conf pars are the same as point source confusion since arm confusion occurs when a (bright) 
    0th order point sources falls on the spectrum of a source of interest. 
    
    Parameters
    ----------
    arm_dict : dictionary
        Arm confusion dict which holds all possible arm confusion entries for every source in main_list.    
    perp_dist_to_spec_arm_par : float
        distance in pixels from the 0th order confusing source 'j' perpendicular to the dispersed arm of the 
        confused source 'i'.
    src_pos_x_par : float
        Positions in physical units associated with sources in the main_list.
    P_arm_par : float
        HEG or MEG gratings period which is an instrumental constant.
    arm_par : str
        HETG 'heg' or 'meg' arm.
    roll_nom_Par : float
        Roll angle of the observation taken from the fits header.
    src_off_axis_par : float
        Off-axis angle of the source in arcseconds
    r0_offset_dist_from_contam_arm_par: float
        This is an offset value needed when calculating the distance between 0th order of the confused source and the 
        0th order of the confuser source.
    counts_par : int
        The number of 0th order counts.
    subset_sources : str
        list of sources to generate confusion files for.
    mm_per_pix : float
        The constant number of millimeters per ACIS pixel. (CONSTANT = 0.023987)
    X_R : float
        Rowland  diameter in millimeters (CONSTANT=8632.48)        

    Returns
    -------
    Updates values in arm_dict and returns dictionary.

    """
    for i in subset_sources:

        if src_off_axis_par[i] < 180:
            off_axis_modifier_i = 1
        elif (src_off_axis_par[i] >= 180 and src_off_axis_par[i] < 360):
            off_axis_modifier_i = 2
        elif src_off_axis_par[i] >= 360:
            off_axis_modifier_i = 3
        else:
            print('ERROR off axis check')	

        for j in range(0,len(src_pos_x_par)):

            if src_off_axis_par[j] < 180:
                off_axis_modifier_j = 1
            elif (src_off_axis_par[j] >= 180 and src_off_axis_par[j] < 360):
                off_axis_modifier_j = 2
            elif src_off_axis_par[j] >= 360:
                off_axis_modifier_j = 3
            else:
                print('ERROR off axis check')	

            #First calculate 0th_counts_frac for the relevant sources
            if i != j and counts_par[i] > 0 and counts_par[j] > min_arm_counts and np.abs(perp_dist_to_spec_arm_par[i,j]) < (max_arm_dist * off_axis_modifier_i * off_axis_modifier_j):
                arm_dict['0th_cnts_frac'][arm_par][i,j] = counts_par[j] / counts_par[i]

            #second, use '0th_cnts_frac' to calcualte arm_confusion location -- Basically identical to point source confusion calculation but with different loop condition.
            if (perp_dist_to_spec_arm_par[i,j] != 0) and (arm_dict['0th_cnts_frac'][arm_par][i,j] > 0):
                arm_dict['intersect_dist'][arm_par][i,j] = abs((src_pos_x_par[j]-src_pos_x_par[i]) / math.sin(math.radians(90-arm_ang_par)) + r0_offset_dist_from_contam_arm_par[i,j])

                for m in ['1','2','3']:
                    if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
                        if src_pos_x_par[j] > src_pos_x_par[i]:
                            arm_dict[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_dict['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number
                        elif src_pos_x_par[j] < src_pos_x_par[i]:
                            arm_dict[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_dict['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number		
                        else:
                            print(f'ERROR in point source confuse calculation for i,j,m = {i,j,m}')													
                    elif (roll_nom_par > 90 and roll_nom_par < 270):
                        if src_pos_x_par[j] < src_pos_x_par[i]:
                            arm_dict[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_dict['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number
                        elif src_pos_x_par[j] > src_pos_x_par[i]:
                            arm_dict[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_dict['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number							
                        else:
                            print(f'ERROR in point source confuse calculation for i,j,m, roll_nom_par = {i,j,m, roll_nom_par}')
                    else:
                        print('ERROR -- Check roll_nom_par value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')


    return(arm_dict)



def determine_confused_order(arm_dict, src_pos_x_par, arm_par):

    """
    Identifies which of the arm orders that the 0th order lands on for later use in arm boundary calculation (dx). 
    Note, for an i,j pair there can only be ONE arm+order the 0th order falls on. 
    
    Parameters
    ----------
    arm_dict : dictionary
        Arm confusion dict which holds all possible arm confusion entries for every source in main_list.    
    src_pos_x_par : float
        Positions in physical units associated with sources in the main_list.
    arm_par : str
        HETG 'heg' or 'meg' arm.

    Returns
    -------
    Updates arm_dict and returns the dictionary
    """

    for i in range(len(src_pos_x_par)):
        for j in range(len(src_pos_x_par)):
            if arm_dict['0th_cnts_frac'][arm_par][i,j] > 0:
                if arm_dict[arm_par+'+1']['wave'][i,j] != 0:	#note, change to easily demonstrate that !=0 means the value is filled and that is then where the confusion occurs between this and negative order. heg+1 and -1 can't both be filled for same source.
                    arm_dict['arm_confused_wave'][arm_par][i,j] = arm_dict[arm_par+'+1']['wave'][i,j]
                elif arm_dict[arm_par+'-1']['wave'][i,j] != 0:
                    arm_dict['arm_confused_wave'][arm_par][i,j] = -1 * arm_dict[arm_par+'-1']['wave'][i,j]  # make the negative order negative
                
    return(arm_dict)


def calc_ccd_energy_res(arm_par):
    
    """
    Creates an array of ACIS resolving power as a function of wavelength for MEG and HEG. Matches a polynomial fit of the 
    ACIS resolving power as a function of energy (fig 6.14 in the proposers obseravtory guide) to the HEG/MEG arms for 
    use in arm_flag_set() when calculating the OSIP boundaries for two sources that suffer arm confusion.

    Parameters
    ----------
    arm_par : str
    HETG 'heg' or 'meg' arm.

    Returns
    -------
    res_power_arm_maxed : ACIS resolving power as a function of wavelength for 'heg' or 'meg'
    hetg_arr_arm : an array of wavelengths at the spectral resolution of 'heg' or 'meg'

    """
    #set the max wavelength and resolution elements for HEG an dMEG
    if arm_par == 'heg' or arm_par == 'HEG':
        max_wave = 16 #must be int
        res_element = 0.01
    elif arm_par == 'meg' or arm_par == 'MEG':
        max_wave = 32 #must be int
        res_element = 0.02
    else:
        raise ValueError('Could not set max_wave or res_element because arm_par could not be identified as meg or heg')

    planck = 4.135667696E-15
    c_speed = 2.9979E8 #m/s

    poly_result = [ 1.12276612e-10, -2.62121212e-06,  2.94110334e-02,  3.13566434e+01]  #note, this is from the best fit 3rd degree polynomial to 10 samples at 1, 2, 3 kev.  poly0 * x^3 + poly1 * x^2 * poly2 * x + ploy3

    ccd_lam_arm = np.arange(0,max_wave, res_element)  #create a wavelength array 
    ccd_lam_arm[0] = 0.0001 # replace the first element of this array with a tiny number that is not zero so it won't affect future calculations (divide by zero issues)
    ccd_E_arm = (planck * c_speed) / (1E-10 * ccd_lam_arm) #convert wavelength array to energy 

    #loop to calculate resolving power (R = de/E) from the best fit poly. Have to calc it for both heg and meg cause step size (in lam) is different 0.01 vs 0.02
    FWHM_poly_arm = [None] * len(ccd_E_arm) 
    for i in range(0,len(FWHM_poly_arm)):
        FWHM_poly_arm[i] = poly_result[0]*ccd_E_arm[i]**3 + poly_result[1]*ccd_E_arm[i]**2 + poly_result[2]*ccd_E_arm[i]**1 + poly_result[3] 

    res_power_arm_positive = ccd_E_arm / FWHM_poly_arm #calc resolving power from 0 to max_wave in A 
    res_power_arm_positive[0] = 6E-4 # manually set so no divide by 0 issues
    res_power_arm = np.zeros(3200)
    res_power_arm[0:1600] = np.flip(res_power_arm_positive[0:1600]) #note something weird going on here with element arrays seems to be off by one but thats ok cause one element is tiny in wavelength space...Not sure why it doesn't perfectly match the hetg_arr_arm
    res_power_arm[1600:3200] = res_power_arm_positive[0:1600]
    hetg_arr_arm = np.arange(-1*max_wave, max_wave, res_element)

    #Ok, there is an issue with this method for very small wavelengths < 1 A which don't have E responses in the figure and the function extrapolation blows them up. So they are modified to top them off at the max rate. 
    res_power_arm_maxed = np.zeros(len(res_power_arm))
    for i in range(0, len(res_power_arm)):
        if (hetg_arr_arm[i] > -1 and hetg_arr_arm[i] < 1):
            res_power_arm_maxed[i] = max(res_power_arm)
        else:
            res_power_arm_maxed[i] = res_power_arm[i]

    return(res_power_arm_maxed, hetg_arr_arm)



def arm_flag_set(arm_dict, arm_par, num_sources, res_power_arm_maxed_par, hetg_arr_arm_par, subset_sources, heg_cutoff_high_par, meg_cutoff_high_par, nsig_par=6):

    """
    When arm confusion occurs, order sorting regions will overlap depending on the distance between the two 0th order 
    point sources (dx). This calculates the wavelength for each order where the dispersed counts of a confuser source 
    will improperly be assigned to the extracted (confused) source. These calculated wavelenghts are saved to 
    ['wave_low'] and ['wave_high'] for each source and the flags are set appropriately (as described below).

    
   Parameters
    ----------
    arm_dict : dictionary
        Arm confusion dict which holds all possible arm confusion entries for every source in main_list. 
    arm_par : str
        HETG 'heg' or 'meg' arm.           
    num_source : int
        Then number of sources in main_list.
    res_power_arm_maxed_par : float, array
        ACIS resolving power as a function of wavelength for 'heg' or 'meg'
    hetg_arr_arm_par : float, array
       Array of wavelengths at the spectral resolution of 'heg' or 'meg'
    subset_sources : str
        list of sources for which to generate confusion files.
    nsig_par : float
        Approximation for how wide the OSIP range is for order sorting when determining which events are part of the 
        Nth order spectrum.
    heg/meg cutoff high : float
        Wavelength in angstroms above which the HEG and MEG effective areas go to zero or the user doesn't care 
        outside this max wavelength bounds.
    
    Returns
    -------
    Updates values in arm_dict and returns dictionary.


    Arm Confusion Flags
    -------------------
    flag_99 : arm is confused from another bright source
    flag_98 : only one of the two +/- orders of an arm is confused because the confuser source distance (dx) is 
        sufficiently large to allow order sorting to mitigate confusion on the other arm
    """

    flag_clean = 'clean'
    flag_warn = 'warn'
    flag_confused = 'confused'

    flag_99 = 'arm_confusion'
    flag_98 = 'opposite order has arm confusion'

    if arm_par == 'heg' or arm_par == 'HEG':
        arm_cutoff_high = heg_cutoff_high_par
    elif arm_par == 'meg' or arm_par == 'MEG':
        arm_cutoff_high = meg_cutoff_high_par
    else:
        raise ValueError('Could not set arm_cutoff_high because arm_par value was not heg or meg')

    for i in subset_sources:
        for j in range(0,num_sources):

            if arm_dict['arm_confused_wave'][arm_par][i,j] != 0:

                arm_confuse_hetg = [None] * len(hetg_arr_arm_par)
                x = hetg_arr_arm_par
                dx = arm_dict['arm_confused_wave'][arm_par][i,j]
                if dx == 0:
                    print(f'Warning, dx=0 for {i,j}')
                
                k_fwhm_sig = np.sqrt(np.log(256))

                arm_confuse_hetg = np.abs( (nsig_par / (res_power_arm_maxed_par * k_fwhm_sig) ) * ( ( 2*x / dx) -1 ) ) #note, this **should** work cause res_power_HEG is on same scale so it should just calculate per array value each one. NEed to check though

                #these need to be initialized so case after logic of diff == 1 doesn't fail. Check.
                hetg_element_low = 0
                hetg_element_high = 0

                bad_arm = sorted(np.where(arm_confuse_hetg >= 1.0))

                #note, might want to include safeguards here in the future. In case it crosses the .9999 to 1.0 boundary more or less than two times! Right now this loop is just saving the most recent time and assuming its twice total
                if len(bad_arm[0]) > 0:
                    for z in range(0,len(bad_arm[0]) - 1):
                        diff = np.abs(bad_arm[0][z] - bad_arm[0][z+1])
                        if diff != 1:
                            if dx < 0:
                                hetg_element_low = bad_arm[0][z]+1
                                hetg_element_high = bad_arm[0][z+1]

                            if dx > 0:		
                                hetg_element_low = bad_arm[0][z]+1
                                hetg_element_high = bad_arm[0][z+1]

                        hetg_low = hetg_arr_arm_par[hetg_element_low]
                        hetg_high = hetg_arr_arm_par[hetg_element_high]
                
                #if this gets executed then it means there was NO arm confusion because dx confuser source was far enough away that order sorting takes care of everything. I assign these variables to the negative version of the arm_cuttoff_wavelength so that the wave_low value will look like 'ignore wave_low 16 to wave_high 16 or meg-1 and meg+1 (in other words ignore nothing). These values are used for the loop logic below so be careful changing. There is probably room for improvement in this method. 
                else:
                    hetg_low = -1*arm_cutoff_high 
                    
                    #these are set because I will ignore them using this logic next if statement. Probably is a better way to address this. If this gets executed that means there is NO arm confusion so 'confused' flag needs to be reset to 'not confused'
                    hetg_high = -1*arm_cutoff_high

                for m in ['1','2','3']:
                    #note-- here I am populating wave_low and wave_high values REGARDLESS of whether there actually is arm confusion determined via OSIP boundaries. Consider putting this in if statement below so its only populated when real confusion occurs.
                    #positive orders
                    arm_dict[arm_par+'+'+m]['wave_low'][i,j] = hetg_high / int(m)
                    arm_dict[arm_par+'+'+m]['wave_high'][i,j] = arm_cutoff_high / int(m)
                    
                    #negative orders
                    arm_dict[arm_par+'-'+m]['wave_low'][i,j] = np.abs(hetg_low) / int(m)
                    arm_dict[arm_par+'-'+m]['wave_high'][i,j] = arm_cutoff_high / int(m)

                    #if both values are pegged at limits then no confusion, otherwise one or both orders are confused.
                    if (hetg_low == (-1*arm_cutoff_high) and hetg_high == (-1*arm_cutoff_high)):
                        arm_dict[arm_par+'+'+m]['flag'][i,j] = flag_clean
                        arm_dict[arm_par+'-'+m]['flag'][i,j] = flag_clean

                    elif (hetg_low == (-1*arm_cutoff_high)):
                        arm_dict[arm_par+'-'+m]['flag'][i,j] = flag_warn
                        arm_dict[arm_par+'-'+m]['flag_comment'][i,j] = flag_98
                        
                        arm_dict[arm_par+'+'+m]['flag'][i,j] = flag_confused
                        arm_dict[arm_par+'+'+m]['flag_comment'][i,j] = flag_99

                    elif (hetg_high == (-1*arm_cutoff_high)):
                        arm_dict[arm_par+'-'+m]['flag'][i,j] = flag_confused
                        arm_dict[arm_par+'-'+m]['flag_comment'][i,j] = flag_99
                        
                        arm_dict[arm_par+'+'+m]['flag'][i,j] = flag_warn
                        arm_dict[arm_par+'+'+m]['flag_comment'][i,j] = flag_98
                    else:
                        arm_dict[arm_par+'+'+m]['flag'][i,j] = flag_confused
                        arm_dict[arm_par+'+'+m]['flag_comment'][i,j] = flag_99

                        arm_dict[arm_par+'-'+m]['flag'][i,j] = flag_confused
                        arm_dict[arm_par+'-'+m]['flag_comment'][i,j] = flag_99										

    return(arm_dict)


####MAIN FLAG SET####


def main_flag_set(conf_dict_par, num_sources, subset_sources):
    """
    Sets the main flag parameters (spec, pntsrc, arm)_conf['flag'] and ['flag_comment'] values based on their 
    respective ['arm+order']['flag'] values. If one source 'i' has no confusion with another source 'j' based on the 
    individual arm/order flags, then the entire source will be determined 'clean' (no confusion). If ALL arm+order 
    flags are a combination of 'clean' and 'warn' then this will set flag to 'warn'. If ANY arm+order flag is 
    'confused' then the flag value is set to 'confused'. This is primarily used in write_conf_table() to remove 
    unnecessary output.

    Note, the order of the 'else-ifs' in this loop are important. Clean flag is only set if 'confused' or 'warn' 
    doesn't trigger first. Consider redoing this flag in a way that doesn't have to loop through so many things.

    Parameters
    ----------
    conf_dict_par : dictionary
        Confusion dictionary which can be spectral confusion, pointsource confusion or arm confusion.
    num_sources : int
        Number of sources in the main_list
    subset_sources : int, list
        List of sources for which to generate confusion files.

    Returns
    -------
    Sets the main flags and returns the input (updated) conf_dict.
    """
    for i in subset_sources:
        for j in range(0,num_sources):
            flag_checker = np.array([], dtype='object')
            flag_warn_comments = ''
            flag_confused_comments = ''				

            for n in ['heg','meg']:
                for m in ['-3','-2','-1','+1','+2','+3']:
                    flag_checker = np.append(flag_checker, conf_dict_par[n+m]['flag'][i,j])
                    if conf_dict_par[n+m]['flag'][i,j] == 'warn':
                        if flag_warn_comments == '':
                            flag_warn_comments = flag_warn_comments+n+m #get rid of extra comma
                        else:
                            flag_warn_comments = flag_warn_comments+','+n+m
                    elif conf_dict_par[n+m]['flag'][i,j] == 'confused':
                        if flag_confused_comments == '':
                            flag_confused_comments = flag_confused_comments+n+m
                        else:
                            flag_confused_comments = flag_confused_comments+','+n+m
            
            if np.all(flag_checker == 'unset'):
                conf_dict_par['flag'][i,j] = 'unset'
            if np.any(flag_checker == 'confused'):
                conf_dict_par['flag'][i,j] = 'confused'
                conf_dict_par['flag_comment'][i,j] = flag_confused_comments
            elif np.any(flag_checker == 'warn'):
                conf_dict_par['flag'][i,j] = 'warn'
                conf_dict_par['flag_comment'][i,j] = flag_warn_comments
            elif np.all((flag_checker == 'clean') | (flag_checker == 'unset')): #this will check if the flag_checker holds values of ONLY 'clean' AND 'unset'. This is necessary because sometiems above I leave some flags unset for arm+order to save CPU time.
                conf_dict_par['flag'][i,j] = 'clean'
            else:
                print(f'ERROR-- something went wrong with the main flag check because no previous loop conditions were met for i,j = {i,j}.')

    return(conf_dict_par)
                



def write_full_conf_table(spec_dict, pntsrc_dict, arm_dict, obsid_par, output_dir_par, srcID_par, counts_par, RA_par, DEC_par, remove_clean = 'yes', row_num=808, consolidate_table = False, cc_table_root=None):

    """
    Extracts a single source (row) from the three nested dictionaries (one for each confusion type) and creates a fits 
    table summarizing the detected confusion parameters. The user has the option of saving every source and their 
    associated parameter values but most of the time there is no confusion and its unneccesary to include everything. 
    Users can filter to only produce tables where confusion occurs (flag='confused') or where confusion was close to 
    occuring (flag='warn'). This is a relatively complex function to accomodate pycrates as a fits-writing tool 
    throughout CrissCross. This function could be made significantly simpler using astropy or pandas tables.

    Parameters
    ----------
    spec_dict, pntsrc_dict, arm_dict : dictionaries
        The final confusion dictionaries for all three types of confusion.
    obsid_par : str
        The obsID value associated with the observations.
    output_dir_par : str
        directory where the confusion output tables will be saved.
    srcID_par : int, list
        The list of element numbers associated with each source in the main_list. 
    counts_par : int
        The number of 0th order counts associated with each source in the main_list.
    RA_par, Dec_par : float
        Right ascension and declination in J2000 degrees associated with the source for which the confusion tables are generated. This value
        is saved in the output table header.
    remove_clean : bool
        'yes' will save all confusion results to table (clean, warn and confused) and 'no' will save only 'warn' and 
        'confused'.
    row_num : int
        The element (row) associated with a source from the main list. This source is the source for which the 
        confusion table is generated.
    consolidate table : bool
        If set to 'True', this will create both a 'full' and a 'consolidated' table. The smaller table is much more 
        readable.
    """


    def set_mask_par(spec_dict, pntsrc_dict, arm_dict, remove_clean, row_num ):
        """
        Sets the mask parameter which identifies the table rows to include in the final output product. If 
        'remove_clean' = 'yes' then the output tables will only show sources that have at least one flag=confused or 
        flag=warn in all of the arms/orders/confusion_type. If 'remove_clean' != 'yes' then all sources are included 
        in the final table. Warning -- if the number of sources are large then this table can become large fast. 

        Parameters
        ---------
        spec_dict, pntsrc_dict, arm_dict : dictionaries
            The final confusion dictionaries for all three types of confusion.
        remove_clean : bool
            'yes' will save all confusion results to table (clean, warn and confused) and 'no' will save only 'warn' and 
            'confused'.
        row_num : int
            The element (row) associated with a source from the main list. This source is the source for which the 
            confusion table is generated.    

        Returns
        -------
        mask par : array
            The elements in the input dictionary that were identified with the remove_clean bool logic.    
        """
        
        if remove_clean == 'yes':
            mask_par = np.where( ((spec_dict['flag'][row_num] == 'confused') | (spec_dict['flag'][row_num] == 'warn')) | ((pntsrc_dict['flag'][row_num] == 'confused') | (pntsrc_dict['flag'][row_num] == 'warn')) | ((arm_dict['flag'][row_num] == 'confused') | (arm_dict['flag'][row_num] == 'warn'))    )[0].tolist()

        else:
            mask_par = None

        return(mask_par)



    def extract_conf_row(confusion_dict, row_num, mask_par):
        """
        Extracts a single row from every array inside the confusion_dict and returns a new nested dictionary with 
        the same structure. This utilizes that mask_parameter from set_mask_par() and will only return the indices 
        included in the mask (if remove_clean = 'yes').

        Parameters
        ---------
        confusion_dict : dictionary
            Any confusion dictionary.
        row_num : int
            The element (row) associated with a source from the main list. This source is the source for which the 
            confusion table is generated.            
        mask par : array
            The elements in the input dictionary that were identified with the remove_clean bool logic.

        Returns
        -------
        filtered_dict : nested dictionary
            Returns a nested dictionary containing a single source (row_num) from the main confusion dictionary. 
        """

        filtered_dict = {}

        for key, value in confusion_dict.items():

            # Case 1: arm+order keys (dict of arrays)
            if isinstance(value, dict) and all(isinstance(v, np.ndarray) for v in value.values()):
                filtered_dict[key] = {}
                for subkey, arr in value.items():
                    if mask_par != None:
                        filtered_dict[key][subkey] = arr[row_num, mask_par]
                    else:
                        filtered_dict[key][subkey] = arr[row_num, :]


            # Case 2: intersect_dist, xintercept, yintercept (dict of heg/meg arrays)
            elif isinstance(value, dict) and set(value.keys()) == {"heg", "meg"}:
                if mask_par != None:
                    filtered_dict[key] = {
                        "heg": value["heg"][row_num, mask_par],
                        "meg": value["meg"][row_num, mask_par]
                    }
                else:
                    filtered_dict[key] = {
                        "heg": value["heg"][row_num, :],
                        "meg": value["meg"][row_num, :]
                    }						

            # Case 3: global arrays (flag, flag_comment)
            elif isinstance(value, np.ndarray):
                if mask_par != None:
                    filtered_dict[key] = value[row_num, mask_par]
                else:
                    filtered_dict[key] = value[row_num, :]
                    
            else:
                raise ValueError(f"Unexpected structure in key '{key}'")

        return(filtered_dict)



    def flatten_confusion_dict(d, parent_key="", sep="_"):
        
        """
        Crates can't take a nested dictionary as an argument so this flattens the dictionary for easy input to crates.

        Returns
        ------
        flat = dictionary
            A flattened (non-nested) confusion dictionary.
        """

        flat = {}
        for key, value in d.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                flat.update(flatten_confusion_dict(value, new_key, sep=sep))
            else:
                # NumPy arrays or any other non-dict values go directly in
                flat[new_key] = value
        return(flat)


    def convert_obj_to_string(flat):
        
        """
        Crates can't accept 'object' datatypes (the flags and flag_comments in the dictionary) so this converts 
        them to strings.

        Returns
        -------
        flat : dictionary
            Returns input dictionary but converting the object datatypes to strings.
        """

        for i in flat:
            if flat[i].dtype == 'O':
                flat[i] = flat[i].astype(str)

        return(flat)


    def merge_conf_crates(conf_crate_par, merged_crate_par):

        """
        Concatenates crate tables (conf_crate_par) to a new 'merged' table. This is used to concatenate the multiple 
        types of confusion (spec, pntsrc and arm) since they are all (mostly) unique.

        Parameters
        ----------
        conf_crate_par : Crate
            Confusion table that has been converted into crate format
        merged_crate_par : Crate
            An empty crate to merge other crates into.
        """

        for colname in conf_crate_par.get_colnames():
            col = conf_crate_par.get_column(colname)
            merged_crate_par.add_column(col)

        return(merged_crate_par)



    def make_flattened_conf_table(conf_par, root_par, mask_par):

        """
        Runs several of the above functions to ultimately create a crates table from a nested dictionary while 
        appending the name of the dictionary (spec, pnt, arm) to the columns. Returns crate for table generation and 
        flattened dict for use in consolidated table.

        Parameters
        ----------
        conf_par : dictionary
            Confusion dictionary
        root_par : str
            Root for naming the types of confusion in the merged crate.
        mask_par : array
            The elements in the input dictionary that were identified with the remove_clean bool logic.

        Returns
        -------
        crate_conf : Crate
            The crate created from a confusion_dict
        flattened_dict : dict
            The flattened (non-nested) dictionary
        """
    
        single_row = extract_conf_row(conf_par, row_num, mask_par)
        flattened_dict = flatten_confusion_dict(single_row)
        flattened_dict = convert_obj_to_string(flattened_dict)
        flattened_dict = { root_par + key: value for key, value in flattened_dict.items() }


        crate_conf = make_table_crate(flattened_dict)

        return(crate_conf, flattened_dict)


    def make_ancillary_crate(srcID_par, counts_par, mask_par, num_sources, obsid_par):
        """
        Add supplementary info to the table such as obsID, srcID and number of 0th order counts before merging 
        all three sources of confusion. 

        Parameters
        ----------
        srcID_par : int
            Adds the srcID (element/row) number associated with the confusing source to the crate table
        counts_par : int
            Adds the number of 0th order counts for each srcID to the crate table
        mask_par : array
            The elements in the input dictionary that were identified with the remove_clean bool logic.
        num_sources : int
            The number of sources in the main_list.
        obsid_par : str
            The obsID associated with the observation.

        Returns
        -------
        anc_crate : crate object
            A new crate with ancillary data added.

        """
        obsid_arr = CrateData()
        srcid_arr = CrateData()
        pntsrc_counts_arr = CrateData()

        obsid_arr.name = 'obsID'
        srcid_arr.name = 'confuser_srcID'
        pntsrc_counts_arr.name = '0th_order_confused_cnts'


        if mask_par == None:            
            obsid_arr.values = np.full(num_sources, int(obsid_par))				
            srcid_arr.values = np.arange(0,num_sources,1)				
            pntsrc_counts_arr.values = counts_par				

        else:
            num_sources = len(mask_par)
            
            obsid_arr.values = np.full(num_sources, int(obsid_par))
            srcid_arr.values = srcID_par[mask_par]
            pntsrc_counts_arr.values = counts_par[mask_par]

        anc_crate = TABLECrate()
        add_col(anc_crate, obsid_arr)
        add_col(anc_crate, srcid_arr)
        add_col(anc_crate, pntsrc_counts_arr)

        #break


        return(anc_crate)


    ###BEGIN TABLE CREATION

    mask_par = set_mask_par(spec_dict, pntsrc_dict, arm_dict, remove_clean, row_num)

    spec_conf_crate, spec_conf_flattened = make_flattened_conf_table(conf_par=spec_dict, root_par='spec_', mask_par = mask_par)
    pntsrc_conf_crate, pntsrc_conf_flattened =  make_flattened_conf_table(conf_par=pntsrc_dict, root_par='pnt_', mask_par = mask_par)
    arm_conf_crate, arm_conf_flattened =  make_flattened_conf_table(conf_par=arm_dict, root_par = 'arm_', mask_par = mask_par)

    ancillary_crate = make_ancillary_crate(srcID_par=srcID_par, counts_par=counts_par, mask_par=mask_par, num_sources=len(spec_dict['flag']), obsid_par=obsid_par)

    merged_crate = TABLECrate()
    
    merged_crate = merge_conf_crates(conf_crate_par = ancillary_crate, merged_crate_par = merged_crate)
    merged_crate = merge_conf_crates(conf_crate_par = spec_conf_crate, merged_crate_par = merged_crate)
    merged_crate = merge_conf_crates(conf_crate_par = pntsrc_conf_crate, merged_crate_par = merged_crate)
    merged_crate = merge_conf_crates(conf_crate_par = arm_conf_crate, merged_crate_par = merged_crate)

    #Add RA and DEC of the confused source to the header of the crates table.
    set_key(merged_crate, name='RA_conf', data=RA_par, unit='deg', desc='RA of src with potential HETG confusion')
    set_key(merged_crate, name='DEC_conf', data=DEC_par, unit='deg', desc='Dec of src with potential HETG confusion')

    #allow users to name table if CrissCross is only run on a single source
    if cc_table_root == None:
        write_file(merged_crate, f'{output_dir_par}/confused_src_{row_num}_full_obsID_{obsid_par}.fits', clobber=True)
    else:
        write_file(merged_crate, f'{output_dir_par}/confused_{cc_table_root}_full_obsID_{obsid_par}.fits', clobber=True)
        

    if consolidate_table == True:

        #create numpy arrays for each consolidated table column to append data to
        #consider making the appending a function so I dont have to repeat.
        confuser_srcid_col = []
        zeroth_order_confused_counts_col = []
        grating_type_col = []
        order_col = []
        confusion_type_col = []
        confusion_wave_col = []
        wave_low_col = []
        wave_high_col = []
        arm_confused_frac_col = []
        flag_col = []
        flag_comment_col = []

        # def fill_cols(conf_type, arm, order):

        #This works on the already filtered flattened_dict table which means only the rows that are part of mask_par are included. That means you can't simply save the [j] values of things in the loop the same way as in previous functions. 
        
        #this will loop through the three sources of confusion via the flattened dictionarys. Consider putting in check to make sure there is at least some values in each conf type
        for conf_class_flat, conf_type in zip([spec_conf_flattened, pntsrc_conf_flattened, arm_conf_flattened],['spec','pnt','arm']):


            for j in range(0,len(mask_par)):
                
                for n in ['heg','meg']:
                    for m in ['-3','-2','-1','+1','+2','+3']:			

                        if conf_class_flat[conf_type+'_'+n+m+'_flag'][j] == 'warn' or conf_class_flat[conf_type+'_'+n+m+'_flag'][j] == 'confused':
                            confuser_srcid_col.append(mask_par[j])
                            zeroth_order_confused_counts_col.append(counts_par[mask_par[j]])
                            grating_type_col.append(n)
                            order_col.append(m)
                            confusion_type_col.append(conf_type)
                            confusion_wave_col.append(conf_class_flat[conf_type+'_'+n+m+'_wave'][j])
                            wave_low_col.append(conf_class_flat[conf_type+'_'+n+m+'_wave_low'][j])
                            wave_high_col.append(conf_class_flat[conf_type+'_'+n+m+'_wave_high'][j])
                            flag_col.append(conf_class_flat[conf_type+'_'+n+m+'_flag'][j])
                            flag_comment_col.append(conf_class_flat[conf_type+'_'+n+m+'_flag_comment'][j])


        consolidated_crate = TABLECrate()

        col0 = CrateData()
        col0.name = 'obsID'
        col0.values = np.full(len(confuser_srcid_col), obsid_par) #gives each table an obsID col for later concatenation

        col1 = CrateData()
        col1.name = 'confuser_srcid'
        col1.values = confuser_srcid_col

        col2 = CrateData()
        col2.name = '0th_order_confused_counts'
        col2.values = zeroth_order_confused_counts_col

        col3 = CrateData()
        col3.name = 'grating_type'
        col3.values = grating_type_col
        
        col4 = CrateData()
        col4.name = 'order'
        col4.values = order_col
        
        col5 = CrateData()
        col5.name = 'confusion_type'
        col5.values = confusion_type_col
        
        col6 = CrateData()
        col6.name = 'confusion_wave'
        col6.values = confusion_wave_col
        
        col7 = CrateData()
        col7.name = 'wave_low'
        col7.values = wave_low_col
        
        col8 = CrateData()
        col8.name = 'wave_high'
        col8.values = wave_high_col

        col9 = CrateData()
        col9.name = 'flag'
        col9.values = flag_col			

        col10 = CrateData()
        col10.name = 'flag_comment'
        col10.values = flag_comment_col	

        add_col(consolidated_crate,col0)	
        add_col(consolidated_crate,col1)	
        add_col(consolidated_crate,col2)	
        add_col(consolidated_crate,col3)	
        add_col(consolidated_crate,col4)	
        add_col(consolidated_crate,col5)	
        add_col(consolidated_crate,col6)	
        add_col(consolidated_crate,col7)	
        add_col(consolidated_crate,col8)	
        add_col(consolidated_crate,col9)	

        #Add RA and DEC of the confused source to the header of the crates table.
        set_key(consolidated_crate, name='RA_conf', data=RA_par, unit='deg', desc='RA of src with potential HETG confusion')
        set_key(consolidated_crate, name='DEC_conf', data=DEC_par, unit='deg', desc='Dec of src with potential HETG confusion')

        #allow users to name table if CrissCross is only run on a single source
        if cc_table_root == None:
            write_file(consolidated_crate, f'{output_dir_par}/confused_src_{row_num}_consolidated_obsID_{obsid_par}.fits', clobber=True)
        else:
            write_file(consolidated_crate, f'{output_dir_par}/confused_{cc_table_root}_consolidated_obsID_{obsid_par}.fits', clobber=True)
            

    #return(merged_crate)
    return()



def end_of_run_cleanup(output_dir_list_par, obsid_par, wavdetect_par=False):
    """
    Cleans up directory at end of CrissCross run. Creates a wavdetect file output folder if CrissCross runs wavdetect 
    and moves the appropraite files there. Also checks the confusion tables to make sure they are not empty 
    (no confusion) and if so it deletes the empty ones.

    Parameters
    ----------
    output_dir_list_par : str
        Output directory where CrissCross files are saved
    obsid_par : str
        ObsID associated with the observation.
    wavdetect_par : bool
        Boolean to identify whether CrissCross ran wavdetect or the user supplied the table on their own. This affects 
        whether wavdetect ancillar files were created and need to be moved to a new dir for cleanup.
    """
    
    #create the directories to hold CrissCross files
    table_dir = f'{output_dir_list_par}/confusion_output_files/table_fits_data'
    os.makedirs(table_dir, exist_ok=True)

    #if CrissCross ran wavdetec then create wavdetect dir and move files there
    if wavdetect_par == True:
        wav_dir = f'{output_dir_list_par}/confusion_output_files/wavdetect_output'
        os.makedirs(wav_dir)
        wave_files = glob.glob(f'{output_dir_list_par}/wavdetect_obsid_{obsid_par}*')
        for i in wave_files:
            shutil.move(i, wav_dir)
        

    #identify the confusion tables that were created and delete the tables that are 'empty' (no confusion) based on known empty file sizes (revisit this in future).
    output_table_full=glob.glob(f'{output_dir_list_par}/confused_*full_obsID_{obsid_par}.fits')
    output_table_consolidated=glob.glob(f'{output_dir_list_par}/confused_*consolidated_obsID_{obsid_par}.fits')

    for i in range(len(output_table_full)):
        file_size_table=os.stat(output_table_full[i])
        if file_size_table.st_size == 46080: #note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the number of columns!
            os.remove(output_table_full[i])

    for i in range(len(output_table_consolidated)):
        file_size_table=os.stat(output_table_consolidated[i])
        if file_size_table.st_size == 5760: #note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the number of columns!
            os.remove(output_table_consolidated[i])

    #move the remaining table files to the table directory
    files_to_move = glob.glob(f'{output_dir_list_par}/confused_*_obsID_{obsid_par}.fits')
    #check that some files exist after removing the tables that have no confusion.
    if len(files_to_move) == 0:
        print('WARNING -- No confusion tables exist after removing empty tables. No confusion identified with input source(s) or something went wrong in CrissCross.')
    else:
        for i in files_to_move:
            shutil.move(i, table_dir)

    return()


def time_logger(mode, time_started=[], time_counter=[], message=[]):
    """
    Creates a time logger and prints relevant steps in the code to the screen. 

    Parameters
    ---------
    mode : str
        Controls much of the logic how function prints info to screen. Options are 'start', 'update', 'end'.
    time_started : time object
        The time at the moment of program execution
    time_counter : int
        A counter to count the number of times the function was run throughout the program.
    message : str
        A message to print to the screen when executed.

    Example usage
    -------------

    time_log_start, time_log_counter = time_logger(mode='start')
    time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, 
    message='message 1')
    time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, 
    message='message 2')

    """
    if mode == 'start':
        time_start = time.time()
        time_log_counter = 0
        time_log_start = time_start

        obj = time.localtime() 
        t = time.asctime(obj)

        print('\n')
        print('CrissCross Time Start:')
        print(t)
        print('\n')

        return(time_log_start, time_log_counter)

    elif mode == 'update':

        time_counter_update = time_counter+1
        time_log_elapsed = round((time.time() - time_started)/60,2)
        time_log_obj = time.localtime() #these three are necessary to print local time in readable format AND its still of by four hours SIGHHH
        
        t_log = time.asctime(time_log_obj)
        print('\n')
        print(f'TIME LOG #{time_counter_update}  -- {message}')
        print(t_log)
        print('%s minutes have elapsed' %(time_log_elapsed))
        print('\n')

        return(time_counter_update)
    
    elif mode == 'end':

        time_stop = time.time()
        total_time = round((time_stop - time_started)/60,2)
        print()
        print(f'total elapsed time has been {total_time} minutes.')
        print()

        return(total_time)

    else:
        print('mode was not set to appropriate value')
        
    return()


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

    #if user enters 'ARF' or 'RMF' then lower case for later glob use
    resp_type_par = resp_type_par.lower() 

    #check to make sure responses are either arf or rmf
    if resp_type_par != 'arf' and resp_type_par != 'rmf':
        raise ValueError('Response type must be either arf or rmf')	

    #load the pha2 file and obtain the crate where relevant information is stored
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)
    
    #identify the number of spectra in the PHA2 file
    num_spec_par = len(spec_crate_par.TG_M.values)

    #determine which pipeline the PHA2 file came from (archive vs CIAO user)
    creator_key = get_keyval(spec_crate_par, 'CREATOR')
    
    if 'Version DS' in creator_key:

        #if users pha2_file_par is a long path or a single file, strip the name and check for the root so the resp glob doesn't get any extra unrelated files in the response dir.
        # Note, the strings in this section are based on the DS standard naming. 
        pha_name = Path(pha2_file_par).name
        pha_root = pha_name.partition('_pha2.fits')[0]

        if resp_dir_par != None: #use provided resp_dir_par
            resp_list_par = glob.glob(f'{resp_dir_par}/{pha_root}*{resp_type_par}2.fits*')
        else:
            pha_dir = Path(pha2_file_par).parent #need to get directory where PHA2 file is located
            resp_list_par = glob.glob(f'{pha_dir}/responses/{pha_root}*{resp_type_par}2.fits*')
            
    elif 'Version CIAO' in creator_key: #this is produced via chandra_repro or user custom spectral extraction
        
        #read the header to search for the PHA2 root name which is often the same root as the responses
        hist = get_history_records(spec_crate_par)
        pha_root = ''  #set to '' for checking later in case pha_root not found

        #if chandra_repro was used to produce the PHA2 file then a ':root" value is saved in the header history. This identifies that value.
        for i in range(0,len(hist)):
            if ':root=' in hist[i][1]: #find the line where the :root command was used
                root_line = hist[i][1].split('=',1)[1].strip() #strip the unnecessary stuff but leaves the extra spaces
                pha_root = root_line.split(' ')[0] #remove everything after the root value
                break #stops searching hist for the appropriate line after it is found

        #if pha_root is not overwritten at this point then throw error because it means it was not found
        if pha_root == '':
            raise ValueError('Could not identify PHA2 file root. Please load responses manually.')

        #use glob and pha_root to find the responses
        if resp_dir_par != None: #use provided resp_dir_par
            resp_list_par = glob.glob(f'{resp_dir_par}/{pha_root}*.{resp_type_par}')
        else:
            pha_dir = Path(pha2_file_par).parent #need to get directory where PHA2 file is located
            resp_list_par = glob.glob(f'{pha_dir}/tg/{pha_root}*.{resp_type_par}') #use the root name of the PHA2 file to ID the responses. This way users can have many extractions in a single dir but it will only grab the appropriate ones.
    
    #if the creator of the PHA2 file is not DS or CIAO then exit.
    else:
        raise ValueError('Cannot determine the creator of PHA2 file and responses will have to be loaded manually')
    
    #check to make sure at least some files were found
    if len(resp_list_par) < 1:
        raise ValueError('Could not identify responses. Please load responses manually.')

    #check that the length of the arf or RMF lists match the number of PHA spec in the PHA2 file
    if len(resp_list_par) != num_spec_par:
        print(f'WARNING-- The identified number of {resp_type_par.upper()}s [{len(resp_list_par)}] does not match the number of PHA spectra [{num_spec_par}] in the PHA2 file. Only the responses found will be included.\n')

    return(resp_list_par)


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

    #check to make sure responses are either arf or rmf
    if resp_type_par != 'arf' and resp_type_par != 'rmf':
        raise ValueError('Response type must be either arf or rmf')

    #reads in the pha2 file and checks how many spectra (orders) it includes.
    pha2_dataset = read_pha(pha2_file_par)
    spec_crate_par = pha2_dataset.get_crate(2)

    #identify the file arrangement of the HETG orders and HEG/MEG arms via the PHA2 file
    tg_m_arr = spec_crate_par.TG_M.values
    tg_part_arr = spec_crate_par.TG_PART.values
    tg_obsid = get_keyval(spec_crate_par, 'OBS_ID')

    #determine the number of spectra in the pha2 file based on the length of one of the tg arrays:
    num_spec_pha2 = len(tg_m_arr)

    #warn user if the number of PHA2 spectra are different than the number of response files (either found automatically or provided manually)
    if len(resp_list_par) != num_spec_pha2:
        print(f'\nWARNING -- The number of {resp_type_par} files [{len(resp_list_par)}] does not equal the number of spectra in the PHA2 file [{num_spec_pha2}]. Only responses that match with a spectrum will be included.\n')

    #create empty lists to later append HEG/MEG arm, order and obsID values from the response files headers
    resp_m_arr = []
    resp_tg_part_arr = []
    resp_obsid_arr = []

    #read each response file and append appropriate header value
    for i in range(0,len(resp_list_par)):
        resp_data = read_file(resp_list_par[i])
        resp_m_arr.append(get_keyval(resp_data, 'TG_M'))
        resp_tg_part_arr.append(get_keyval(resp_data, 'TG_PART'))
        resp_obsid_arr.append(get_keyval(resp_data, 'OBS_ID'))

    #convert obsid lists to numpy arrays for later use with np.where() for obsID checking
    tg_obsid = np.array(tg_obsid)
    resp_obsid_arr = np.array(resp_obsid_arr)

    #create an empty object array the same size as the PHA2 file (number of spectra) to hold either 'no match' or the path to the matched response file
    matched_resp_list_par = np.array(['']*num_spec_pha2, dtype='object')

    #for each spectra, use tg_m, tg_part and obsID to match to a single response file. Print appropriate errors.
    for i in range(0,num_spec_pha2):
        match_resp = np.where((resp_m_arr == tg_m_arr[i]) & (resp_tg_part_arr == tg_part_arr[i]) & (resp_obsid_arr == tg_obsid))[0].tolist()
        if len(match_resp) == 1:
            matched_resp_list_par[i] = resp_list_par[match_resp[0]] #this is the element in the response array that match the i_th element of the PHA2 file.
        elif len(match_resp) > 1:
            raise ValueError(f'ERROR, more than one {resp_type_par.upper()} match found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}. ')
        elif len(match_resp) == 0:
            matched_resp_list_par[i] = 'no match'
            print(f'Warning, no {resp_type_par.upper()} found for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}.')
        else:
            raise ValueError(f'ERROR - Something with wrong identifying {resp_type_par.upper()}s for TG_M={tg_m_arr[i]}, TG_PART={tg_part_arr[i]} and obsID={tg_obsid}')

    #report the files matched to the screen in a nice format so it is clear it worked or didn't work
    print('\nThe following response files were found\n')

    #name the arm and order something more readable for output message
    arm = lambda x: 'HEG' if x==1 else 'MEG' if x ==2 else 'ERROR'
    order = lambda x: f'+{x}' if x > 0 else f'-{-1*x}' if x < 0 else 'ERROR'

    print()
    for i in range(0,num_spec_pha2):		
        print(f'{arm(tg_part_arr[i])+order(tg_m_arr[i])} -- {resp_type_par.upper()}: {matched_resp_list_par[i]}')
    print()

    #returns the array of matched responses in the same order as the PHA2 spectra
    return(matched_resp_list_par)



def clean_spec(cc_table, pha_file, spec_root, arf_file=None, resp_dir=None):

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

    """

    def convert_order(order_int):
        """
        Converts an integer to a string with a + or - sign in front of it (e.g., '+1' or '-1'; for compatibility with CrissCross cleaning table)
        """
        if order_int > 0:
            return(f'+{order_int}')
        elif order_int < 0:
            return(f'-{-1*order_int}')
        else:
            raise ValueError('0th order is included and that is not compatible with clean_spec')
        
    def convert_arm(tg_part_val):
        """
        Converts the HETG tg_part value to a string (e.g., 'heg' or 'meg'; for compatibility with CrissCross cleaning table)
        """
        if tg_part_val == 1:
            return('heg')
        elif tg_part_val == 2:
            return('meg')
        else:
            raise ValueError(f'Arm cannot be identified')


    def clean_data(cc_table, pha_crate, arf_data_var, pha_arm_var, pha_order_var, pha_element, conf_flag_var = 'confused'):
        """
        Creates copies of the relevant PHA1/PHA2 and ARF columns and modifies them (sets to zero) using a CrissCross 
        confusion table. 
        
        Parameters
        ----------

        cc_table: fits table
            CrissCross produced confusion table for a single source and single obsID.
        pha_crate: Crate object
            The Crate data for a single spectrum (e.g., HEG+1)
        arf_data_var: Crate object
            The Crate data for a single ARF response matched to a spectrum (e.g., HEG+1)
        pha_arm_var: int (1 or 2)
            The tg_part value associated with the spectrum (1 = HEG, 2 = MEG)
        pha_order_var: int (-3, -2, -1, 1, 2, 3)
            The order associated with the spectrum (e.g., 1 for HEG+1 and -3 for MEG-3)
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
        
        #reads in the confusion and PHA data
        cc_data = read_file(cc_table)
        pha_data_var = pha_crate.get_crate(2)

        #PHA1 and PHA2 files have to be treated slightly differently because of how crates stores values. This is to avoid having to slice off each crate spectrum from the PHA2 file.
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
            specresp_arr = arf_data_var.SPECRESP.values #ARFs are not in PHA2 (array) format and thus don't need a pha_element
            fracexpo_arr = arf_data_var.FRACEXPO.values #ARFs are not in PHA2 (array) format and thus don't need a pha_element
            bin_low_arr = pha_data_var.BIN_LO.values[pha_element]
            bin_high_arr = pha_data_var.BIN_HI.values[pha_element]	

        else:
            raise ValueError('PHA datatype must be 1 or 2')		


        #copies the counts and stat_err column of the PHA file for modification
        cleaned_spec_var = counts_arr.copy()
        cleaned_staterr_var = stat_err_arr.copy()

        #copies the SPECRESP and fracexpo columns from the arf
        cleaned_specresp_var = specresp_arr.copy()
        cleaned_fracexpo_var = fracexpo_arr.copy()

        #for every row of the confusion table that match the input PHA spectrum order and tg_part, identify the elements (rows) associated with wavelengths (bin_low and bin_hi) that need to be cleaned. Note, this assumes the PHA bin_lo and bin_hi values are identical to the ARF file (which should be the case).
        for i in range(0,len(cc_data.wave_low.values)):
            if cc_data.flag.values[i] == conf_flag_var and cc_data.grating_type.values[i] == pha_arm_var and cc_data.order.values[i] == pha_order_var:
                elements_to_clean = np.where( (bin_low_arr >= cc_data.wave_low.values[i]) & (bin_high_arr <= cc_data.wave_high.values[i]) ) #identify elements
                
                #clean PHA (spectrum)
                cleaned_spec_var[elements_to_clean] = 0. #set elements that overlap to zero
                cleaned_staterr_var[elements_to_clean] = 1.86603 #double check that this makes sense and the stat_err is always this value for zero counts. I suspect instead I should take min of this column and set it to that.

                #clean ARF (response)
                cleaned_specresp_var[elements_to_clean] = 0.
                cleaned_fracexpo_var[elements_to_clean] = 0.

        #return the cleaned arrays values.
        return(cleaned_spec_var, cleaned_staterr_var, cleaned_specresp_var, cleaned_fracexpo_var)


    #Read the PHA file and determine if PHA1 or PHA2. Uses read_pha() to bring along the necessary PHA extensions.
    pha_crate_dataset = read_pha(pha_file)
    
    if is_pha_type1(pha_crate_dataset):

        pha_data = pha_crate_dataset.get_crate(2) #Crate 2 contains the PHA data
        arf_data = read_file(arf_file)

        #determine the heg/meg arm, order and obsID of the PHA spectrum and make sure it matches the ARF
        tg_part = get_keyval(pha_data, 'TG_PART') #tg_part = 1 = heg; tg_part = 2 = meg
        tg_m = get_keyval(pha_data, 'TG_M')
        tg_obs = get_keyval(pha_data, 'OBS_ID')
        tg_part_arf = get_keyval(arf_data, 'TG_PART')
        tg_m_arf = get_keyval(arf_data, 'TG_M')
        tg_obs_arf = get_keyval(arf_data, 'OBS_ID')

        #if parameters dont match between ARF and PHA then throw error
        if tg_obs != tg_obs_arf or tg_m != tg_m_arf or tg_part != tg_part_arf:
            raise ValueError('One of the following is not consistent between the PHA file and ARF: HEG/MEG arm, order, obsID')

        #use clean_data() to create copies of the appropriate PHA and ARF arrays where wavelenghts with confusion are set to 0
        cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(cc_table = cc_table, pha_crate = pha_crate_dataset, arf_data_var = arf_data, pha_arm_var = pha_arm, pha_order_var = pha_order, pha_element=0, conf_flag_var = 'confused')

        #replaces the original arrays in the loaded crates with the new arrays
        pha_data.COUNTS.values = cleaned_spec
        pha_data.STAT_ERR.values = cleaned_staterr
        arf_data.SPECRESP.values = cleaned_specresp
        arf_data.FRACEXPO.values = cleaned_fracexpo

        #appends the original files to the history for record keeping
        pha_data.add_record("HISTORY", f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ")
        arf_data.add_record("HISTORY", f"This cleaned ARF was created using the ARF file: {arf_file} and the CrissCross cleaning table: {cc_table}. ")

        update_crate_checksum(pha_data)
        update_crate_checksum(arf_data)

        #setup tgpart and order to be consistent with values in confusion tables for file naming.
        pha_arm = convert_arm(tg_part)
        pha_order = convert_order(tg_m)

        #saves a new file while maintaining the original header.
        write_pha(pha_crate_dataset, f'{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.pha', clobber=True)
        write_file(arf_data, f'{spec_root}_obsid_{tg_obs}_{pha_arm}{pha_order}_cleaned.arf', clobber=True)


    #PHA2 files need to be treated a little different because they are arrays of arrays and order/arm info is not in header. Also the arfs may be out of order if user provides a list of arfs.
    elif is_pha_type2(pha_crate_dataset):

        #if user enters their own arf or list of arfs then make sure they match the PHA2 file format (e.g., pha2 meg+1 has to be same array element as arf meg+1)
        if arf_file != None:
            if type(arf_file) == str:
                arf_file = list([arf_file]) #make sure arf_file variable is a list just in case user enters a single file as 'file1' instead of ['file1'].

            #check and arrange that the user input arf file(s) are in the correct order of the PHA2 spectra. matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(pha2_file_par=pha_file, resp_list_par = arf_file, resp_type_par='arf')

        #if user doesn't enter arfs then try to find them either using the user included response dir or the standard CIAO-produced file structure
        else:
            print('Warning, no ARF response files provided in parameter arf_file. Attempting to find them.')
            resp_list = find_resp_files(pha2_file_par=pha_file, resp_type_par='arf', resp_dir_par=resp_dir)

            if len(resp_list) == 0:
                raise ValueError('No response files found. Try including a directory with resp_dir_par or include a list of response paths with arf_file parameter.')
            
            #matched_resp_list will create an array that matches the PHA2 format.
            matched_resp_list = match_resp_order(pha2_file_par=pha_file, resp_list_par = resp_list, resp_type_par='arf')

        #read the PHA data and obtain the tg_m, tg_part and obsID values
        pha_data_full = pha_crate_dataset.get_crate(2)
        
        tg_m_arr = pha_data_full.TG_M.values
        tg_part_arr = pha_data_full.TG_PART.values
        tg_obs = get_keyval(pha_data_full, 'OBS_ID')

        #convert order and arm parameters into format consistent with confusion tables for file-naming purposes only
        pha_order_arr = []
        for i in tg_m_arr:
            pha_order_arr.append(convert_order(order_int=i))

        pha_arm_arr = []
        for i in tg_part_arr:
            pha_arm_arr.append(convert_arm(tg_part_val=i))


        #only run clean_data() for the spectra that have a matched response file so identify which elements of the matched_resp_list have both a spectrum and associated ARF.
        spec_to_clean = np.where(matched_resp_list != 'no match')[0] #note, the 'no match' string comes from match_resp_order() so be careful if that changes.

        #run clean_data() for every arm and order which have a spectrum and matching ARF
        for i in spec_to_clean:
            
            arf_data = read_file(matched_resp_list[i]) # load the arf from match_resp_list because it is already matched to the appropriate PHA2 file

            cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(cc_table = cc_table, pha_crate = pha_crate_dataset, arf_data_var = arf_data, pha_arm_var = pha_arm_arr[i], pha_order_var = pha_order_arr[i], pha_element = i, conf_flag_var = 'confused')

            #replaces the original arrays with the new arrays
            pha_data_full.COUNTS.values[i] = cleaned_spec
            pha_data_full.STAT_ERR.values[i] = cleaned_staterr
            arf_data.SPECRESP.values = cleaned_specresp
            arf_data.FRACEXPO.values = cleaned_fracexpo

            #update the ARF header and write out the file
            arf_data.add_record("HISTORY", f"This cleaned ARF was created using the ARF file: {matched_resp_list[i]} and the CrissCross cleaning table: {cc_table}. ")
            update_crate_checksum(arf_data)

            write_file(arf_data, f'{spec_root}_obsid_{tg_obs}_{pha_arm_arr[i]}{pha_order_arr[i]}_cleaned.arf', clobber=True)


        #appends the original files to the history of the new file for record keeping
        pha_data_full.add_record("HISTORY", f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ")

        update_crate_checksum(pha_data_full)

        #saves a new PHA2 file while maintaining the original header.
        write_pha(pha_crate_dataset, f'{spec_root}_obsid_{tg_obs}_cleaned.pha2', clobber=True)


    else:
        raise ValueError('Input PHA file was not a PHA1 or PHA2 type file')

    return()	




######### MAIN CrissCross RUN FUNCTION ##############

def run_crisscross(cc_outdir = 'criss_cross_output', arf_ratios_dir = 'input_files', main_list = 'input_files/full_coup_src_list.tsv', subset_src_list = 'input_files/subset_onc.tsv', clean_single_RA=None, clean_single_DEC=None, clean_single_root=None, evt2_file=None, wavdetect_file=None, clobber_par=False, max_pntsrc_dist=8, min_pntsrc_counts=5,min_spec_counts=3, min_spec_confuser_counts=50, osip_frac=1.0, spec_confuse_limit=0.1, max_arm_dist=8, min_arm_counts=50, arm_nsig=6.0, meg_cutoff_low=1.0, meg_cutoff_high=32.0, heg_cutoff_low=1.0, heg_cutoff_high=16.0):
    """
    Main function for running criss cross. CrissCross identifies portions of a sources spectrum where events from other
    field sources may be errouneously assigned to the extracted source with standard CIAO processing. CrissCross
    produces a fits table for each source which tabulates the wavelength location where confusion occurs for all HETG
    arms (heg+meg) and orders -3 to +3. CrissCross requires the evt2 file that was used to extract a source's spectra 
    and a list of RA+DEC (main_list) for every X-ray source in the field of view. A list of sources in the field of 
    view can often be obtained by running wavdetect on the same field if there are non-HETG archival Chandra 
    observations. CrissCross can create spectral confusion tables for all sources present in a secondary 
    (subset_src_list) list or can be run for a single source using the 'clean_single_RA/DEC' parameters.

    If users have PHA files extracted using the relevant evt2 file they can run clean_spec() using the CrissCross 
    confusion tables as input to remove confused counts from their spectra before performing their spectral analysis.

    Parameters
    ----------
    cc_outidr : str
        A directory for holding the output of CrissCross. If it does not exist then it will be made.
    arf_ratios_dir : str
        The directory which holds the ARF response ratios fits tables necessary for Crisscross.
    main_list : str
        A tsv or ascii file with columns RA, DEC, ID of source positions. This is used to distinguish real sources in a
        wavdetect source table from false sources (identified from the dispersed spectra). This can include sources 
        outside of an individual chandra obsID FOV.
    subset_src_list : str
        A tsv or ascii file of sources to create confusion tables for. This should be a subset of main_list and include 
        sources bright enough for HETG spectral extraction. The table format requires columns RA, and DEC.
    clean_single_RA, clean_single_DEC : float
        RA and DEC for a single source if the user wishes to create only one confusion table. Format must be 
        J2000 degrees.
    evt2_file : str
        A single evt2 file or a list of evt2 files which contain sources in main_list and subset_src_list.
    wavdetect_file : str, None
        A single wavdetect source fits table or a list of wavdetect source fits tables. This is the '*src.fits' file 
        output from wavdetect. If no files are included (e.g., wavdetect_file=None) then wavdetect will be run during 
        execution of CrissCross.
    clobber_par : bool
        If clobber_par = True then CrissCross overwrites previous CrissCross run if output directory already exists.
    
    Special Parameters
    ------------------
    max_pntsrc_dist : int
        Field sources whose 0th order position is less than or equal to this distance, measured in ACIS pixels
        perpendicular from the dispersed spectrum of an extracted source, will be included as potential point source 
        confusion (default: 8).
    min_pntsrc_counts : int
        Field sources with 0th order event counts greater than this threshold will be considered for potential point
        source confusion (default: 5).
    min_spec_counts : int
        Minimum number of 0th order counts for an extracted source to be considered bright enough to consider whether 
        field sources can cause confusion (default: 3).        
    min_spec_confuser_counts : int
        Minimum number of 0th order counts for a field source to be considered bright enough to disperse spectra and
        potentially contaminate the spectrum of an extracted source (default: 50).
    osip_frac : float
        A fraction from 0. to 1. denoting the portion of an OSIP (Order Sorting Integrated Probability) range to be 
        used in the spectral intersection calculation. 1.0 means 100% of the OSIP window is used (default: 1.0).
    spec_confuse_limit : float
        The fraction of dispersed events allowed in a spectral confusion region before deciding the region is 
        contaminated (and thus later ignored in spectral fitting). A value of 0.1 means if confuser 'Src B' contributes
        more than 10% of counts in the confused portion of the spectrum of 'Src A' then the spectral region of Src A is 
        flagged as confused. Note: The number of counts from each source in the affected spectral intersection region 
        (wavelength range) is estimated using the HETG instrument effeciency (ARF) and the number of 0th order counts 
        from each source within the wavelength range (default: 0.1).
    max_arm_dist : float
        Two bright sources whose 0th order distance, measured in ACIS pixels perpendicular from one soruce to the 
        dispersed spectrum of an extracted source, is less than this will be considered as potential arm confusion. 
        Users can increase this parameter if they believe spectra are unfairly being flagged as arm confused. Note: an 
        on-axis spectrum has a width of approximately 5 pixels and thus if two on-axis sources are within 10 pixels 
        then it is possible they can contaminate eachother (default: 8.0).
    arm_nsig : float
        Approximation for how wide the OSIP range is for order sorting when determining which events are part of the 
        Nth order spectrum. This parameter is for arm confusion only and increasing it will cause larger portions of a
        spectrum to be considered confused by arm confusion (default: 6.0).     
    min_arm_counts : int
        The minimum number of 0th order counts a confuser source can have before being considered a candidate for arm 
        confusion. Note, while it depends on the spectrum, if a 0th order source has 50 counts then there are only 
        approximately (1.3 * 50) = 65 dispersed counts in the sum of all arms (HEG/MEG) and orders (default: 50).
    meg_cutoff_low, meg_cutoff_high : float
        The wavelength boundaries for all confusion calculations in Angstroms. If users only care about e.g., the 5-10 
        A region of meg then they can set meg_cutoff_low=5.0 and meg_cutoff_high=10.0 and only confusion that occurs 
        within this wavelength region is considered. This parameter is not used for arm confusion (default: 1.0, 32.0).
    heg_cutoff_low, heg_cutoff_high : float
        The wavelength boundaries for all confusion calculations in Angstroms. If users only care about e.g., the 5-10 
        A region of meg then they can set heg_cutoff_low=5.0 and heg_cutoff_high=10.0 and only confusion that occurs 
        within this wavelength region is considered. This parameter is not used for arm confusion (default: 1.0, 16.0).
    
    """

    ################CONTSTANTS ###############
    X_R = 8632.48 #rowland diameter in mm constant 
    P_meg = 4001.95 #period in angstroms constant. Note, this is value from telD1999-07-23geomN0006.fits in CALDB however in marxsim it uses 4001.41 A
    P_heg = 2000.81 
    mm_per_pix = 0.023987  #pixel size in mm for acis same for I and S;  pix size in arcsec is 0.492'' 
    ###############################

    #sanitize clobber
    if clobber_par == 'True':
        clobber_par = True
    if clobber_par == 'False':
        clobber_par = False

    #sanitize the evt2_file input so it is a list
    if evt2_file == None:
        raise ValueError('Please provide an evt2 file')
    #convert a single file into a list so it can work with loop
    elif type(evt2_file) == str:
        evt2_file = [evt2_file]
    elif type(evt2_file) != list:
        raise ValueError('Unknown type of input for evt2_files. Please include a single file or a list of files')

    if wavdetect_file != None:
        if type(wavdetect_file) == str:
            wavdetect_file = [wavdetect_file]
        elif type(wavdetect_file) != list:
            raise ValueError('Unknown type of input for wavdetect_file. Please include a single file or a list of files')
    
    #check to make sure the number of evt2 files match the number of wavdetect source lists
    if wavdetect_file != None and len(wavdetect_file) != len(evt2_file):
        raise ValueError('The number of input evt2_files and wavdetect source fits table files do not match. Please include a wavdetect table for each evt2 file.')
    
    #run wavedetect_match_obsid before the loop starts to ensure input files are in correct order. Make wavdetect_file a list of [None]s so it can work per obsID in CrissCross loop below.
    if wavdetect_file != None:
        wavdetect_file = wavedetect_match_obsid(fits_list_par = evt2_file, wavdetect_list_par = wavdetect_file)
    else:
        wavdetect_file = [None]*len(evt2_file)
    
    #Start major CrissCross loop for all input evt2 files
    for k in range(len(evt2_file)):

        #ardlib.punlearn()

        #start the time logger for printing steps to the screen
        time_log_start, time_log_counter = time_logger(mode='start')

        #print the tweakable paramters to the screen and then record them near the end along with the time it took to run.
        print('\n')
        print('This run is for observation %s' % evt2_file[k])
        if wavdetect_file[k] != None:
            print('This run is using the wavedetect file %s' %wavdetect_file[k])
        print('The contamination offset threshold is set to %s pixels.' %max_pntsrc_dist)
        print('The counts threshold to be considered a spectrum of interest is set to %s counts.' % min_spec_counts)
        print('The counts threshold to be considered a potential contaminating spectral source is %s counts.' %min_spec_confuser_counts)
        print('The counts threshold to be considered a potential 0th order point source contaminating source is %s counts.' %min_pntsrc_counts)
        print('The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is %s pixels' % max_arm_dist)
        print('The fraction of the OSIP window to include when considering two arm overlaps is set at %s percent ' % (osip_frac*100))
        print('The minimum counts in Src Bs 0th order to assess total arm confusion in source A is %s ' % (min_arm_counts))

        #set a few obsid_specific parameters
        obsid = get_header_par(fits_file = evt2_file[k], keyword_par = 'obs_id')
        roll_nom = float(get_header_par(fits_file = evt2_file[k], keyword_par = 'ROLL_NOM'))
        grating_rotang = read_file(f'{evt2_file[k]}[REGION]') #always reads the region block because the block number is variable
        heg_ang = grating_rotang.ROTANG.values[1] #tg_part = 1
        meg_ang = grating_rotang.ROTANG.values[2] #tg_part = 2

        print('The HEG/MEG angles for this observation are %s and %s degrees.' % (heg_ang, meg_ang))

        print('The roll angle of this observation is %s' % roll_nom)

        #create the output files directory but if clobber=False and it exists then stop CrissCross
        output_dir, dir_exists = make_output_dir(cc_outdir, obsid, clobber_par = clobber_par)
        if dir_exists == True and clobber_par == False:
            print(f'\nClobber set to false and output directory {output_dir} exists. If you wish to overwrite files please set clobber=True\n')
            continue

        #run wavdetect if the user did not input a wavdetect source table. 
        run_wave = False
        if wavdetect_file[k] == None:
            run_wave = True #set so end_of_run_cleanup knows to make output dir and move wavdetect files
            wavdetect_file[k] = run_wavdetect(evt2_file[k], outdir=output_dir, outroot=f'wavdetect_obsid_{obsid}')
            #wavdetect_file[k] = [wavdetect_file]

        #save the RA, DEC and SRCID from the main input list
        RA_wcs, DEC_wcs, srcID = load_sourcelist(filename=main_list)

        #save the RA, DEC from the subset input list or the user input individual source
        if clean_single_RA == None and clean_single_DEC == None:
            subset_RA, subset_DEC = load_sourcelist(filename=subset_src_list, subset_list=True)
        else:
            subset_RA = [float(clean_single_RA)]
            subset_DEC = [float(clean_single_DEC)]

        #match the element number of the subset list to the main list using RA and DEC to 6 digits accuracy.
        subset_list = match_subset_to_main(RA_main=RA_wcs, DEC_main=DEC_wcs, RA_sub=subset_RA, DEC_sub=subset_DEC)

        #convert from RA/DEC in degrees to Chandra Sky physical coordinates and determine off-axis angle in arcsec
        src_pos_x, src_pos_y, src_off_axis = calc_physical_coords(fits_par=evt2_file[k], RA_par = RA_wcs, DEC_par = DEC_wcs)

        time_message = 'Finished converting RA/DEC into chandra coords'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #match input source list to wavedetect table to catalog 0th order counts for each source in each obsid
        final_match_arr, final_dist_arr, counts = find_closest_source(src_x = src_pos_x, src_y = src_pos_y, wave_file = wavdetect_file[k], max_offset = 3.0)

        #create an output file of the input source list with the wave-detect-matched 0th order counts
        write_matched_file(srcid_par = srcID, ra_par = RA_wcs, dec_par = DEC_wcs, counts_par = counts, fileroot = f'{output_dir}/src_list_{obsid}')

        #Print to the screen the number of sources that satisfy the above conditions as well as the total number of sources in input list.
        src_num = len(src_pos_x)

        counts_intercept_num = len(counts[counts > min_spec_counts]) #will count the number of sources that are above the threshold

        print("The total number of sources input is %s." % (src_num))
        print("The number of sources above the contamination intercept threshold of %s counts for ObsID %s is %s." % (min_spec_counts,obsid, counts_intercept_num))

        #calculate relevant parameters for when two lines intersect in the Chandra FOV
        m_heg, m_meg, b_heg, b_meg, xintercept_heg, xintercept_meg, yintercept_heg, yintercept_meg, xoff, yoff = determine_line_intersect_values(src_pos_x_par = src_pos_x, src_pos_y_par = src_pos_y, heg_ang_par = heg_ang, meg_ang_par = meg_ang)

        time_message = 'Finished calculating XY intercepts for all sources in the field of view.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #########SPECTRAL CONFUSION START ############

        #create the spectral confusion nested dictionary for all sources before filling in values using the next functions.
        spec_conf = conf_dict(num_sources = len(src_pos_x), highest_order = 3)

        #Calculate where two spectral arms intersect eachother for every source 
        spec_conf = spec_confuse_wave(spec_conf, src_pos_x, src_pos_y, 'heg', xintercept_heg, yintercept_heg, counts, min_spec_counts, min_spec_confuser_counts, P_heg, 3, roll_nom_par = roll_nom, mm_per_pix=mm_per_pix, X_R=X_R)
        spec_conf = spec_confuse_wave(spec_conf, src_pos_x, src_pos_y, 'meg', xintercept_meg, yintercept_meg, counts, min_spec_counts, min_spec_confuser_counts, P_meg, 3, roll_nom_par = roll_nom, mm_per_pix=mm_per_pix, X_R=X_R)

        time_message = 'Finished calculating where two spectral amrs intersect for all sources.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #Calculate the wave_low and wave_high bounds for spectral confusion which is based on the HETG geometry
        spec_conf = spec_confuse_wave_bounds(spec_conf, highest_order= 3, num_sources = len(src_pos_x))

        #Determine OSIP wavelength range expected at the location and energy of spectral confusion for each source.
        spec_conf = spec_calc_osip_bounds(spec_conf, osip_frac_par = osip_frac, subset_sources = subset_list, num_sources = len(src_pos_x), fits_list_par=evt2_file[k], obsid_par = obsid, outdir=output_dir)

        time_message = 'Finished calculating OSIP wavelengths for spectral confusion.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #determine whether spectral confusion has occured and set the appropriate arm/order flags
        spec_conf = spec_flag_set(spec_conf, src_pos_x_par = src_pos_x, src_pos_y_par = src_pos_y, subset_sources = subset_list, fits_list_par = evt2_file[k], arf_ratios_dir_par = arf_ratios_dir, spec_confuse_limit_par=spec_confuse_limit,heg_cutoff_low= heg_cutoff_low, heg_cutoff_high=heg_cutoff_high, meg_cutoff_low=meg_cutoff_low, meg_cutoff_high=meg_cutoff_high)

        time_message = 'Finished assigning spectral confusion.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #########POINT SOURCE CONFUSION START ############

        #CREATE the point source confusion dictionary to hold all relevant parameters
        pntsrc_conf = conf_dict(num_sources = len(src_pos_x), highest_order = 3)

        #calcluates perp_distance_to_spec and 'intersect distance' for all point sources
        pntsrc_conf, perp_dist_to_spec_heg, r0_offset_dist_from_contam_heg = pntsrc_dist_to_spec(pntsrc_dict=pntsrc_conf, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, xoff_par=xoff, yoff_par=yoff, m_arm_par=m_heg, b_arm_par=b_heg, arm_ang_par=heg_ang, arm_par='heg')

        pntsrc_conf, perp_dist_to_spec_meg, r0_offset_dist_from_contam_meg = pntsrc_dist_to_spec(pntsrc_dict=pntsrc_conf, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, xoff_par=xoff, yoff_par=yoff, m_arm_par=m_meg, b_arm_par=b_meg, arm_ang_par=meg_ang, arm_par='meg')	

        #Determines the wavelegth where point source confusion may occur 

        #HEG
        pntsrc_conf = pntsrc_confuse_wave(pntsrc_dict=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg ,src_pos_x_par=src_pos_x, P_arm_par=P_heg, mm_per_pix=mm_per_pix, X_R=X_R, arm_par='heg', roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, counts_par=counts, max_pntsrc_dist_par=max_pntsrc_dist, min_spec_counts_par=min_spec_counts, min_pntsrc_counts_par=min_pntsrc_counts)

        #MEG
        pntsrc_conf = pntsrc_confuse_wave(pntsrc_dict=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, src_pos_x_par=src_pos_x, P_arm_par=P_meg, mm_per_pix=mm_per_pix, X_R=X_R, arm_par='meg', roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, counts_par=counts, max_pntsrc_dist_par=max_pntsrc_dist, min_spec_counts_par=min_spec_counts, min_pntsrc_counts_par=min_pntsrc_counts)

        time_message = 'Finished calculating point source confusion wavelengths.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #determine whether confusion occurs for all point sources
        pntsrc_conf = pntsrc_confuse_wave_bounds(pntsrc_dict=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg, fits_list_par = evt2_file[k], subset_sources=subset_list, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, arm_par='heg', evt_frac_thresh=0.1, logfile_par=f'{output_dir}/pnt_src_confuse_{obsid}_log.txt')

        pntsrc_conf = pntsrc_confuse_wave_bounds(pntsrc_dict=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, fits_list_par = evt2_file[k], subset_sources=subset_list, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, arm_par='meg', evt_frac_thresh=0.1, logfile_par=f'{output_dir}/pnt_src_confuse_{obsid}_log.txt')

        #sets the flags for point source confusion
        pntsrc_conf = pntsrc_flag_set(pntsrc_dict=pntsrc_conf, num_sources=len(src_pos_x), arm_par='heg', subset_sources = subset_list, meg_cutoff_low_par=meg_cutoff_low, meg_cutoff_high_par=meg_cutoff_high, heg_cutoff_low_par=heg_cutoff_low, heg_cutoff_high_par=heg_cutoff_high)
        pntsrc_conf = pntsrc_flag_set(pntsrc_dict=pntsrc_conf, num_sources=len(src_pos_x), arm_par='meg', subset_sources = subset_list, meg_cutoff_low_par=meg_cutoff_low, meg_cutoff_high_par=meg_cutoff_high, heg_cutoff_low_par=heg_cutoff_low, heg_cutoff_high_par=heg_cutoff_high)

        time_message = 'Finished assigning point source confusion.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)		

        ##########ARM CONFUSION START ############################

        #creates the arm confusion nested dictionary based on the total number of source in the input list
        arm_conf = arm_conf_dict(num_sources = len(src_pos_x), highest_order = 3)

        #Calculates the ratio of 0th order counts (net_counts_confuser / net_counts_confused) and determines the distance from the confused 0th order to the confuser 0th order.
        arm_conf = arm_confuse_wave(arm_dict=arm_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg, src_pos_x_par=src_pos_x, P_arm_par=P_heg, arm_par='heg', arm_ang_par=heg_ang, roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, r0_offset_dist_from_contam_arm_par=r0_offset_dist_from_contam_heg, counts_par = counts, subset_sources = subset_list, mm_per_pix_par=mm_per_pix, X_R_par=X_R, min_arm_counts=min_arm_counts, max_arm_dist=max_arm_dist)
        
        arm_conf = arm_confuse_wave(arm_dict=arm_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, src_pos_x_par=src_pos_x, P_arm_par=P_meg, arm_par='meg', arm_ang_par=meg_ang, roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, r0_offset_dist_from_contam_arm_par=r0_offset_dist_from_contam_meg, counts_par = counts, subset_sources = subset_list, mm_per_pix_par=mm_per_pix, X_R_par=X_R, min_arm_counts=min_arm_counts, max_arm_dist=max_arm_dist)

        #determine which of the positive or negative order the confuser 0th order source falls on
        arm_conf = determine_confused_order(arm_dict=arm_conf, src_pos_x_par = src_pos_x, arm_par = 'heg')
        arm_conf = determine_confused_order(arm_dict=arm_conf, src_pos_x_par = src_pos_x, arm_par = 'meg')

        #calcluates the resolution as a function of energy for heg/meg
        #NOTE--> these values only need to be calculated once PER RUN. Doesn't depend on obsid or location or anything.
        res_power_heg_maxed, hetg_arr_heg = calc_ccd_energy_res(arm_par='heg')
        res_power_meg_maxed, hetg_arr_meg = calc_ccd_energy_res(arm_par='meg')

        #Based on the distance between 0th orders for arm confusion, determine the wavelength range where arm confusion occurs FOR EACH ORDER and set flags appropriately
        arm_conf = arm_flag_set(arm_dict=arm_conf, arm_par='heg', num_sources = len(src_pos_x), res_power_arm_maxed_par=res_power_heg_maxed, hetg_arr_arm_par=hetg_arr_heg, subset_sources = subset_list,heg_cutoff_high_par=heg_cutoff_high, meg_cutoff_high_par=meg_cutoff_high, nsig_par=arm_nsig)
        arm_conf = arm_flag_set(arm_dict=arm_conf, arm_par='meg', num_sources = len(src_pos_x), res_power_arm_maxed_par=res_power_meg_maxed, hetg_arr_arm_par=hetg_arr_meg, subset_sources = subset_list,heg_cutoff_high_par=heg_cutoff_high, meg_cutoff_high_par=meg_cutoff_high, nsig_par=arm_nsig)

        time_message = 'Finished assigning arm confusion.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        #Set MAIN flag for every source pair (if there is any confusion of any type in any order then flag as confused)

        #using the results of the individual confusion functions above, set the main confusion flag for every source. E.g., if any order is confused then main confusion flag is set to 'confused'.
        spec_conf = main_flag_set(conf_dict_par = spec_conf, num_sources = len(src_pos_x), subset_sources = subset_list)
        pntsrc_conf = main_flag_set(conf_dict_par = pntsrc_conf, num_sources = len(src_pos_x), subset_sources = subset_list)
        arm_conf = main_flag_set(conf_dict_par = arm_conf, num_sources = len(src_pos_x), subset_sources = subset_list)

        #Call write_full_conf_table to produce the 'full' and 'consolidated' confusion tables for each source in the run obsID. 
        for i in subset_list:
            #If users run cc with just a single source, allow them to name the confusion file. Otherwise a single root will get clobbered when looped over multiple sources.
            if clean_single_RA != None and clean_single_DEC != None and clean_single_root != None:
                write_full_conf_table(spec_dict = spec_conf, pntsrc_dict = pntsrc_conf, arm_dict = arm_conf, row_num = i, srcID_par = srcID, counts_par = counts, output_dir_par = output_dir, remove_clean = 'yes', obsid_par = obsid, RA_par=RA_wcs[i], DEC_par=DEC_wcs[i], cc_table_root=clean_single_root, consolidate_table = True)
            else:
                write_full_conf_table(spec_dict = spec_conf, pntsrc_dict = pntsrc_conf, arm_dict = arm_conf, row_num = i, srcID_par = srcID, counts_par = counts, output_dir_par = output_dir, remove_clean = 'yes', obsid_par = obsid, RA_par=RA_wcs[i], DEC_par=DEC_wcs[i], consolidate_table = True)


        #move output files into final directories and cleanup
        end_of_run_cleanup(output_dir_list_par = output_dir, obsid_par = obsid, wavdetect_par=run_wave)

        time_message = 'Finished Running CrissCross!.'
        time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

        log_file = open(f'{output_dir}/LOG_{obsid}.txt', 'w')	
        
        log_file.write('This run is for observation %s. \n' % evt2_file[k])
        log_file.write('The wavdetect source list used for this observation is %s. \n' % wavdetect_file[k])
        log_file.write('The roll angle of this observation is %s degrees. \n' % round(roll_nom,2))
        log_file.write('MEG angle = %s degrees and HEG angle = %s degrees. \n' % (round(meg_ang,2),round(heg_ang,2)))
        if roll_nom > 80 and roll_nom < 100:
            log_file.write('WARNING, ROLL NOM IS %s so plus and minus grating orders may be confused and then everything could be wrong. \n' % roll_nom)
        if roll_nom > 260 and roll_nom < 280:
            log_file.write('WARNING, ROLL NOM IS %s so plus and minus grating orders may be confused and then everything could be wrong. \n' % roll_nom)
        log_file.write('\nThe contamination offset threshold is set to %s pixels. \n' %max_pntsrc_dist)
        log_file.write('The counts threshold to be considered a spectrum of interest is set to %s counts. \n' % min_spec_counts)
        log_file.write('The counts threshold to be considered a potential contaminating spectral source is %s counts. \n' %min_spec_confuser_counts)
        log_file.write('The counts threshold to be considered a potential 0th order point source contaminating source is %s counts. \n' %min_pntsrc_counts)
        log_file.write('The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is %s pixels. \n' % max_arm_dist)
        log_file.write('The fraction of the OSIP window to include when considering two arm overlaps is set at %s percent. \n' % (osip_frac*100))
        log_file.write('\nThe total number of sources input is %s. \n' % (src_num))
        log_file.write('The number of sources above the contamination intercept threshold of %s counts for ObsID %s is %s. \n' % (min_spec_counts,obsid, counts_intercept_num))
        log_file.write('The minimum counts in Src Bs 0th order to assess total arm confusion in source A is %s. \n ' % (min_arm_counts))

        log_file.write('The HEG/MEG angles for this observation are %s and %s degrees. \n ' % (heg_ang, meg_ang))	

        if roll_nom > 80 and roll_nom < 100:
            log_file.write('WARNING, ROLL NOM IS %s. Confusion results from roll angles very close to 90 degrees may be incorrect' % roll_nom)
        
        if roll_nom > 260 and roll_nom < 280:
            log_file.write('WARNING, ROLL NOM IS %s. Confusion results from roll angles very close to 270 degrees may be incorrect' % roll_nom)

        total_time = time_logger(mode='end',time_started=time_log_start)

        log_file.write('\nThe total elapsed time for obsID %s is %s minutes. \n' % (obsid, total_time))

        log_file.close()
        






        