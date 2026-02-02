#See README.me for general info about CrissCross


#1/12/26 -- THINGS TO DO STILL

#figure out best way for users to input necessary files (fits, tables, wavdetect stuff)

#CrissCross needs to know the number of 0th order counts associated with each source in an observation's field of view. As such, a wavedetect sourcelist table is necessary for crisscross to match known sources in FOV via an input list to the wavedetect table results. Wavedetect results alone can't be used because wavedetect will detect tons of erroneous sources from the dispersed HETG events. This complicated step can be mitigated if one could run wavedetect using a list of input sources so the wavedetect output would exclusively be detected sources within some threshold of an input source. Alternatively, one could try to use the input source list and dmstat to estimate the number of 0th order counts but then you would need to use off-axis angle and PSF size to get accurate aperture. Perhaps I could get this to work with counts_circl_band in widthofexlusion.py?

#include a function to modify the PHA files for each confused source to mark confused regions as bad for spectral fitting.

#add back in ds9 figure generation so users can see where confusion occurs on the evt2 fits image.

#create tutorial for using code with a simple case

#add functionality for user-supplied list of 0th order sources and their counts (instead of matching to a wavedetect table)

#add functionality for user to calculate confusion between two selected sources in a field of view and print results to screen.

#make code more efficient



##########################################################################################
##########################################################################################
##########################################################################################


import numpy as np
import matplotlib.pyplot as plt
import os
import math
import subprocess
import glob
import shutil
from ciao_contrib.runtool import *
import time 
from iocaldb import OSIP, Sky2Chandra  #moritz's point source extraction contribution
from widthofexclusion import * #moritz's point source extraction contribution
from pycrates import read_file, write_file, TABLECrate, CrateData, add_col, add_record, get_keyval, read_pha, write_pha, is_pha_type1, is_pha_type2, update_crate_checksum
from crates_contrib.utils import make_table_crate
import csv




############################################################


######## THRESHOLD PARAMS SET ********************************************************************************

#users can tweak these paramters to make the confusion calculations more/less conservative. In most cases, users should leave these as default.

#PNTSRC CONFUSION
contam_offset_thresh = 8 #threshold in pixels for how far a point source can be perpendicular from the dispersed spectrum it may contaminate (confuse). 
counts_contam_pntsrc_thresh = 5 #threshold to be flagged as a point source that is bright enough to contaminate the extracted sources spectrum

#SPECTRAL CONFUSION
counts_intercept_thresh_j= 50  #threshold to be flagged as a source bright enough to disperse enough counts to confuse a different sources extracted spectrum.
osip_frac = 1.0 #This controls the size of the OSIP window for cases of two spectra intersection. 1.0 means keep 100% of the window (most conservative). If you want to do 90% of window then this value becomes 0.9.
spec_confuse_limit = 0.1 #fraction of dispersed confusing events allowed before deciding spectral region is contaminated. 0.1 means if Src B contributs more than 10% of counts in the confused region of Src A then it is considered confusion.

#ARM CONFUSION
dist_to_super_bright_perp = 8 #This is used to flag when TWO sources are both bright enough and close enough that their entire arms overlap. This is the perpendicular distance in physical (pixel) between the 0ther order of one source and a line perp to the other source dispersed spectrum. Note, cross dispersion distance is 2.39 arcsec above AND below grating center. so 2.39'' / 0.49 arcsec per pixel gives 5 pixels. If two sources are within 10 pixels of each other they could be contaminating. Consider making this not an optional parameter but hardcoded.
min_HETG_counts = 50 #The minimum number of 0th order counts a CONFUSER source can have before being considered a candidate for ARM confusion. If the 0th order has 50 counts or less than the dispersed number of counts throughout the entire spectrum will be much smaller and thus less likely to cause confusion. 

#Multiple confusion types
counts_intercept_thresh_i = 3  #threshold to be flagged as a source bright enough to care about if another source's dispersed spectra or another 0th order intersects with it 



#HETG INSTRUMENT WAVELENGTH BOUNDS

#Added meg/heg bounds as a parameter choice here. Since ACIS instrument contamination (not HETG confusion) is time dependent, users may wish it 'not care' if potential confusion can occur at e.g., 30A because some of their targets would not expect to have counts there anyway. 

meg_cutoff_low = 1.0 #Angstrom before which the instrument is not sensitive so not worth plotting (blank space between zeroth order and dispersed spectrum)
meg_cutoff_high = 32.0
heg_cutoff_low = 1.0 #note about cutoff, if line has width you have to be careful cause it could get removed from program but still show up in real spectrum so loosen tolerance.
heg_cutoff_high = 16.0

#***********************************************************************************************************************



################CONTSTANTS ###############

X_R = 8632.48 #rowland diameter in mm constant 
P_meg = 4001.95 #period in angstroms constant. Note, this is value from telD1999-07-23geomN0006.fits in CALDB however in marxsim it uses 4001.41 A
P_heg = 2000.81 
mm_per_pix = 0.023987  #pixel size in mm for acis same for I and S;  pix size in arcsec is 0.492'' 

###############################



#############FUNCTION DEFINITIONS###############


def make_output_dir(working_dir):
	"""""
	Creates the working directory if it doesn't already exist
	"""""
	os.makedirs(working_dir, exist_ok = True)



def get_header_par(fits_file, keyword_par):
	"""""
	Use CIAO tool dmkeypar to retrieve a keyword
	"""""

	dmkeypar.punlearn()
	a = dmkeypar(infile=fits_file, keyword=keyword_par)
	return_val = dmkeypar.value

	return(return_val)


#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#See wavedetect open question at top 
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

def wavedetect_match_obsid(fits_list_par, wavedetect_list_par):
	"""
	Uses the obsID header from the evt files (fits_list) and wavedetect source tables (wavedetect_list) to make sure the user input wavedetect_list is in the approrpriate order (e.g., evt2 obsid = wavedetect obsid)
	"""

	fits_obsid = []
	wave_obsid = []

	wavedetect_sorted = []

	for i in range(0,len(fits_list_par)):
		wave_obsid.append(get_header_par(fits_file = wavedetect_list_par[i], keyword_par = 'obs_id'))
		fits_obsid.append(get_header_par(fits_file = fits_list_par[i], keyword_par = 'obs_id'))

	for i in range(0,len(fits_list_par)):
		for j in range(0,len(wave_obsid)):
			if fits_obsid[i] == wave_obsid[j]:
				wavedetect_sorted.append(wavedetect_list_par[j]) 

	return(wavedetect_sorted)
	


def load_sourcelist_csv(filename):
	"""""
	Loads in source and subset lists
	"""""

	RA = []
	DEC = []
	ID = []

	with open(filename, newline='') as f:
		readfile = csv.DictReader(f)
		for row in readfile:
			RA.append(row["RA"])
			DEC.append(row["DEC"])
			ID.append(row["ID"])    
	
	RA = np.array(RA, dtype=float)
	DEC = np.array(DEC, dtype=float)
	ID = np.array(ID, dtype = int)

	f.close()

	return(RA, DEC, ID)



def calc_physical_coords(fits_par, RA_par, DEC_par, celfmt_par = 'deg', option_par = 'cel'):
	""""
	Converts from RA and DEC in WCS to Chandra physical coordinates using dmcoords.
	"""""

	src_pos_x_par=np.zeros(len(RA_par))
	src_pos_y_par=np.zeros(len(DEC_par))


	for i in range(0,len(RA_par)):
		dmcoords.punlearn()
		dmcoords.ra = RA_par[i]
		dmcoords.dec = DEC_par[i]
		dmcoords.infile = fits_par
		dmcoords.celfmt=celfmt_par
		dmcoords.option=option_par
		a = dmcoords()
		src_pos_x_par[i] = dmcoords.x
		src_pos_y_par[i] = dmcoords.y


	return(src_pos_x_par, src_pos_y_par)



def find_closest_source(src_x_arr, src_y_arr, wave_file, max_offset = 3.0):
	""""
	Identifies the closest matching source in a group to a single source based on Chandra SKY physical coordinates only. If multiple matches are found for a single source within max_offset, only the closest of the matches is assigned to the source. This avoids 'double counting'. This function utilizes the positions of sources in the user-provided 'main_list' and matches them to the standard output table of a CIAO wavedetect file. This is necessary because wavedetect is not meant to be run on HETG observations and thus will include many 'false' detections from the dispersed spectra. This function will match the 'true' sources from the user-provided source list to the closest matches in the wavedetect table and return the number of NET_COUNTS associated with 0th order (non-dispersed) detections. NET_COUNTS are used throughout CrissCross to determine the severity of confusion.
	
	max_offset = The max distance in arcsec two sources can be before they are no longer considered matchable between the source list and the wavedetect source table. All sources are treated the same regardless of off-axis angle.
	
	"""""


	#ACIS parameters for converting distance from pixels to arcseconds
	acis_platescale = 48.82E-6 #meters/arcsec
	acis_pix_size = 24E-6 #meters / pixel (square pixels)
	acis_arcsec_per_pix = acis_pix_size / acis_platescale

	#read in and assign relevant wavdetect columns

	wave_data = read_file(wave_file)

	src_wave_x_arr = wave_data.POS.X.values
	src_wave_y_arr = wave_data.POS.Y.values
	counts_wave = wave_data.NET_COUNTS.values


	closest_dist_arr = np.empty(len(src_x_arr), dtype='float') #holds the distance in arcsec to the closest matching source from the wavedetect table
	closest_match_arr = np.empty(len(src_x_arr), dtype='int') #holds the index value from the wavedetect table that is the closest match to a source in the source list.
	
	#these will hold the values above for the matched source AFTER you remove double matches and sources > max_offset.
	final_match_arr = np.empty(len(src_x_arr), dtype=object)
	final_dist_arr = np.empty(len(src_x_arr), dtype=object)

	matched_0th_counts_arr = np.empty(len(src_x_arr), dtype='float') #the final 0th_order counts array (NET_COUNTS) from the wavedetect table MATCHED to the user-provided source list.

	#this loop determines the distance from the user provided source to ALL the sources in the wavedetect table and only saves a non-bogus value if there is a source with separation < max_offset.
	for i in range(0,len(src_x_arr)):
		
		dist_arr = []
		dist_arr = np.sqrt( (src_x_arr[i] - src_wave_x_arr)**2 + ( src_y_arr[i] - src_wave_y_arr)**2  ) #This calculates the physical distance from source [i] in the user-provided table to ALL sources in the wavedetect table. This is just the hypotenuse in the xy plane. Note, calculating the ENTIRE array here for each [i] source and NOT each [i] and each [j] individually. 
		
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
	for i in range(0,len(src_x_arr)):
		
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



def write_matched_file(srcid_arr, ra_arr, dec_arr, counts_arr, fileroot = 'matched_source_list', output_type = 'txt'):
	"""""
	Creates a csv or txt file to save SrcID, RA, Dec and wave_detect_matched 0th order counts.
	"""""

	filestack = np.column_stack((srcid_arr, ra_arr, dec_arr, counts_arr))

	if output_type == 'csv':
		np.savetxt(fileroot+'.csv', filestack, delimiter=',', fmt=['%d', '%.6f', '%.6f', '%.1f'], header = 'ID,RA,DEC,0th_counts', comments='') #need comments to get rid of extra # sign
	if output_type == 'txt':
		np.savetxt(fileroot+'.txt', filestack, delimiter='\t', fmt=['%d', '%.6f', '%.6f', '%.1f'], header = 'ID,RA,DEC,0th_counts', comments='')

	return()



def calc_off_axis_angle(fits_list_par, src_pos_x_par, src_pos_y_par):
	"""""
	Calculates the off-axis angle for each source.
	"""""
	observation_pointing_RA = get_header_par(fits_file = fits_list_par, keyword_par = 'RA_PNT')
	observation_pointing_DEC = get_header_par(fits_file = fits_list_par, keyword_par = 'DEC_PNT')		

	
	dmcoords.punlearn()
	dmcoords.ra = observation_pointing_RA
	dmcoords.dec = observation_pointing_DEC
	dmcoords.infile = fits_list_par
	dmcoords.celfmt='deg'
	dmcoords.option='cel'
	a = dmcoords()
	obsid_pointing_physical_RA = dmcoords.x
	obsid_pointing_physical_DEC = dmcoords.y

	src_off_axis = np.zeros(len(src_pos_x_par))

	src_off_axis = 0.492 * np.sqrt(np.abs(src_pos_x_par - obsid_pointing_physical_RA)**2 + np.abs(src_pos_y_par - obsid_pointing_physical_DEC)**2)

	return(src_off_axis)



def determine_line_intersect_values(src_pos_x_par, src_pos_y_par, heg_ang_par, meg_ang_par):
	""""
	This function solves the equation where two lines (e.g., dispersed spectra) intersect and saves relevant information for use in later functions. Since this info is relevant to both spectral confusion and point source confusion it is its own function.
	"""""

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





def conf_dict(num_sources, highest_order):
	"""""
	This dictionary holds all of the relevant data for confusion between two sources. The format of this dictionary is spec_confuse['arm+order'][parameter][i,j] where 'i' is the potentially CONFUSED source and 'j' is the potential CONFUSER source. For example, spec_confuse['meg-1']['wave'][5,10] shows that the meg arm of srcID=5 has potential confusion in the -1 order from the dispersed spectrum of SrcID=10. The value of the 'wave' parameter in this dictionary entry is the wavelength in angstrom where the spectral confusion occurs. Both spectral confusion and point source confusion share this dictionary format but in separate variables.

	arm values are 'heg' or 'meg'
	valid arm orders are [-3,-2,-1,+1,+2,+3]

	confusion_dict['intersect_dist'] = The distance in pixels between the 0th order src i and the location where confusion may occur from source j
	confusion_dict['xintercept'] = The X location (physical coords) where there is an intersection of gratings between i and j.
	confusion_dict['yintercept'] = The Y location (physical coords) where there is an intersection of gratings between i and j.
	confusion_dict['flag'] = primary flag which represents potential sources of confusion for ALL orders between source i and j.
	confusion_dict['flag_comment'] = primary flag description which represents potential sources of confusion for ALL orders between source i and j.

	confusion_dict['arm+order']['wave'] = the wavelength where confusion may occur
	confusion_dict['arm+order']['wave_low'] = the lower bounds of where confusion may occur
	confusion_dict['arm+order']['wave_high'] = the upper bounds of where confusion may occur
	confusion_dict['arm+order']['osip_low'] = the lower bounds of the OSIP window at the location and wavelength where confusion may occur
	confusion_dict['arm+order']['osip_high'] = the upper bounds of the OSIP window at the location and wavelength where confusion may occur
	confusion_dict['arm+order']['flag'] = the flag which represents potential sources of confusion for a paritcular order between source i and j.
	confusion_dict['arm+order']['flag_comment'] = the flag description which represents potential sources of confusion for a paritcular order between source i and j.
	
	"""""

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


def spec_confuse_wave(spec_conf_arr, src_pos_x, src_pos_y, armtype, xintercept, yintercept, counts, counts_intercept_thresh_i, counts_intercept_thresh_j, period_arm, highest_order, roll_nom_par):
	"""""
	Calculates the distance from the 0th order of src i to the location where confusion may occur ['intersect_dist'] and converts that into wavelength in angstroms ['wave'] using the gratings equation.
	"""""

	# #assign the x,y intercepts to the spec_conf_array. Note, this is done in sort of a weird way cause it was an after thought but for now it should stay. code below uses x/y intercept parameter instead of spec_conf_arr[xyintercept]].
	if armtype == 'heg':

		spec_conf_arr['xintercept']['heg'] = xintercept
		spec_conf_arr['yintercept']['heg'] = yintercept

	if armtype == 'meg':

		spec_conf_arr['xintercept']['meg'] = xintercept
		spec_conf_arr['yintercept']['meg'] = yintercept			


	order_arr = np.arange(1, highest_order+1)

	if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
		for i in range (len(src_pos_x)):
			for j in range (len(src_pos_x)):		
				spec_conf_arr['intersect_dist'][armtype][i,j] = np.sqrt( (src_pos_x[i]-xintercept[i,j])**2 + (src_pos_y[i]-yintercept[i,j])**2)
				if src_pos_x[i] != xintercept[i,j] and xintercept[i,j] > src_pos_x[i] and counts[i] > counts_intercept_thresh_i and counts[j] > counts_intercept_thresh_j: 
					for k in order_arr:
						spec_conf_arr[armtype+'+'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_conf_arr['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
				elif src_pos_x[i] != xintercept[i,j] and xintercept[i,j] < src_pos_x[i] and counts[i] > counts_intercept_thresh_i and counts[j] > counts_intercept_thresh_j:
					for k in order_arr:
						spec_conf_arr[armtype+'-'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_conf_arr['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number

	elif (roll_nom_par > 90 and roll_nom_par < 270):
		for i in range (len(src_pos_x)):
			for j in range (len(src_pos_x)):
				spec_conf_arr['intersect_dist'][armtype][i,j] = np.sqrt( (src_pos_x[i]-xintercept[i,j])**2 + (src_pos_y[i]-yintercept[i,j])**2)
				if src_pos_x[i] != xintercept[i,j] and xintercept[i,j] < src_pos_x[i] and counts[i] > counts_intercept_thresh_i and counts[j] > counts_intercept_thresh_j: 
					for k in order_arr:
						spec_conf_arr[armtype+'+'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_conf_arr['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
				elif src_pos_x[i] != xintercept[i,j] and xintercept[i,j] > src_pos_x[i] and counts[i] > counts_intercept_thresh_i and counts[j] > counts_intercept_thresh_j:
					for k in order_arr:
						spec_conf_arr[armtype+'-'+str(k)]['wave'][i,j] = np.around(( period_arm * ( (spec_conf_arr['intersect_dist'][armtype][i,j]*mm_per_pix )/X_R) ) / float(k), decimals=3) #divide by order number
	else:
		print('Check ROLL_NOM value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')	


	return(spec_conf_arr)




def spec_confuse_wave_bounds(spec_conf_arr, highest_order, src_pos_x_par, heg_bound = 0.68, meg_bound = 1.33):

	"""""
	The sets the wave_low and wave_high spectral confusion windows for every source ASSUMING there is spectral confusion. Fixed distances based on the intersection geometry (which should be 120 pixels: 1.33 A for MEG and 0.68 A for HEG) should be used instead of the OSIP bounds. This calculation is done for ALL sources but only those flagged with confusion will be treated as such. The OSIP range is still used later to quantify how many spectral confusion counts lie in the confusion region for flagging and then these smaller bounds are used when ignoring parts of the spectrum.
	"""""

	#heg_bound and meg_bound are in units of Angstrom and represent the entire window (bounds). It is no recommended to go smaller than the default values as they are determined based on the intstrument.

	#need the keys AND the order numbers in string format
	keys_list = list(spec_conf_arr.keys())
	keys_list.remove('intersect_dist')
	keys_list.remove('xintercept')
	keys_list.remove('yintercept')
	keys_list.remove('flag')
	keys_list.remove('flag_comment')


	for i in range(0,len(src_pos_x_par)):	#loop through each instance of spectral confusion for each source
		for j in range(0, len(src_pos_x_par)):
			for m in keys_list: #one of the keys is 'intersect' so I can't loop through just keys. I need to make sure I'm just looking through the arms (which have subkeys wave and flag)
			
				if spec_conf_arr[m]['wave'][i,j] != 0 and i != j:	#only calculate wave_low and wave_high for sources that have a confusion wavelength calculated 
					if 'heg' in m:
						spec_conf_arr[m]['wave_low'][i,j] = spec_conf_arr[m]['wave'][i,j] - (heg_bound/2)
						spec_conf_arr[m]['wave_high'][i,j] = spec_conf_arr[m]['wave'][i,j] + (heg_bound/2)
					if 'meg' in m:
						spec_conf_arr[m]['wave_low'][i,j] = spec_conf_arr[m]['wave'][i,j] - (meg_bound/2)
						spec_conf_arr[m]['wave_high'][i,j] = spec_conf_arr[m]['wave'][i,j] + (meg_bound/2)

	return(spec_conf_arr)



def spec_calc_osip_bounds(spec_conf_arr, highest_order, subset_arr_par, src_pos_x_par, fits_list_par, obsid_par, osip_frac_par = osip_frac):
	"""""
	Determines the OSIP (order sorting integrated probabilities) window (['osip_low'] and ['osip_high']) at the location on the detector where confusion may have occured. CIAO will use the OSIP tables to determine a valid range of energies (wavelength) to assign to each order based on the expected wavelength at the specific location on the detector (along the grating arm). If a confusing source happens to disperse light at this same location then all events within the OSIP range will be 'accepted' and thus confusion may have occured only within these bounds. In practice, the OSIP wavelength range can be quite large and is only used as a first filter to determine if confusion could occur. More strict confusion checking is done in spec_flag_set().  
	"""""

	#remove non-order-specific keys for easy looping below.
	keys_list = list(spec_conf_arr.keys())
	keys_list.remove('intersect_dist')
	keys_list.remove('xintercept')
	keys_list.remove('yintercept')
	keys_list.remove('flag')
	keys_list.remove('flag_comment')

	#call the OSIP only once per observation
	osip = OSIP(fits_list_par)

	spec_confuse_log_file = open("spec_confuse_"+obsid_par+"_log.txt", "w")
	planck_time_c = (4.1357E-15 * 2.998E18) #conversion for E = hc/lamda where h and c are units of plancks const and angstrom/s
	
	for i in subset_arr_par:
		for j in range (len(src_pos_x_par)):
			for m in keys_list:

				if 'heg' in m:

					if spec_conf_arr[m]['wave'][i,j] != 0: #dont run for sources with no potential confusion
						energy_low = []
						energy_high = []
						frac_osip = []
						results = []

						#calc osip for each subset source
						results = osip(spec_conf_arr['xintercept']['heg'][i,j], spec_conf_arr['yintercept']['heg'][i,j], (planck_time_c/spec_conf_arr[m]['wave'][i,j]), spec_confuse_log_file)

						energy_low, energy_high, frac_resp = results
						
						#convert osip from energy to angstrom and account for user parameter osip_frac (fractional size of osip window of choice --e.g., user could want smaller than large osip window)
						spec_conf_arr[m]['osip_low'][i,j] = planck_time_c/energy_high + (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )
						spec_conf_arr[m]['osip_high'][i,j] = planck_time_c/energy_low - (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )	

				if 'meg' in m:

					if spec_conf_arr[m]['wave'][i,j] != 0:
						energy_low = []
						energy_high = []
						frac_resp = []
						results = []

						results = osip(spec_conf_arr['xintercept']['meg'][i,j], spec_conf_arr['yintercept']['meg'][i,j], (planck_time_c/spec_conf_arr[m]['wave'][i,j]), spec_confuse_log_file)

						energy_low, energy_high, frac_resp = results

						#convert osip from energy to angstrom and account for user parameter osip_frac (fractional size of osip window of choice --e.g., user could want smaller than large osip window)
						spec_conf_arr[m]['osip_low'][i,j] = (planck_time_c/energy_high) + (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )
						spec_conf_arr[m]['osip_high'][i,j] = (planck_time_c/energy_low) - (   (  (1-osip_frac_par) * (planck_time_c/energy_low) - (1-osip_frac_par) * (planck_time_c/energy_high)  ) / 2.0  )	
						
	spec_confuse_log_file.close()
	return(spec_conf_arr)



def spec_flag_set(spec_conf_arr, src_pos_x_par, src_pos_y_par, subset_arr_par, fits_list_par, input_dir_par, highest_order=3):

	"""
	This function sets the spec_conf[arm+order]['flag'][i,j] for spectral confusion (two arms intersecting). This function works in the following way:

	(1) Check all sources against eachother and if two sources don't intersect then assign their 'spectral' confusion flag as 'clean'.

	(2) Run the following checks only for the cases where spectral arms intersect and flag appropriately:

		(a) If the confuser source intersects the arm of the (potentially) confused source outside of the heg/meg cutoff energies (<1 A or >~ 16, 32 A) of the confused source then NO ORDERS of the confuser source could confuse so assign a warning flag (flag_995) 

		(b) If the intersection occurs in the valid range of wavelengths for meg/heg then check the following for EACH order:
			
			(i) Is the confuser's m order wavelength range within the bounds of HEG/MEG? If not, set warning flag (flag_996) and check other orders
			
			(ii) If (i) is TRUE, is the confuser's m order within the same wavelength range as the confused source is expecting at the location of the intersection (i.e., the OSIP window of the confused source at the intersection location)? If not, mark as 'clean' unless a previous order has been flagged as 'warn' or 'confused'
			
			(iii) If (ii) is TRUE then calculate the number of 0th order counts of the CONFUSER source within the OSIP range for the spectral intersection location. If confuser source 0th order has 0 counts then no need to check for confusion anymore and set 'warning' flag. If confuser 0th order has > 0 counts then determine the number of 0th order counts from the CONFUSED source in the OSIP range. Use the number of 0th order counts for both sources and the HEG/MEG-0th-order-to-nth-order ARF tables to estimate the number of dispersed counts from both sources landing in the intersection spot of the potentially confused source. Use ratio of estimated dispersed counts to determine if confusion occurs and flag appropriately. 
			
			NOTE--> This calculation should account for the heg/meg order efficiencies and ARFs BUT assumes an on-axis source at the pointing location. This WILL be slightly different for any other source but to first order it should be ok.   This calculation uses the AVERAGE response ratio in the calculated OSIP range. If OSIP range is large then you are washing out some details in the arfs but for estimation purposes it should be ok.

	Spectral Confusion Flag Definitions:

		'clean' -- This source [i] does not have any confusion from other source [j] in the arm/order listed.
		'warn' -- This source should not have any confusion from other sources in the arm/order listed. However, certain confusion requirements were met but determined to not sufficiently cause confusion.
		'confused' -- This source is confused by some other source and the listed wavelength range should not be used for spectral fitting without accounting for the confuser.

		#Flag Numbers

		99 -- no confusion, i=j or spec_conf_arr[m]['wave'][i,j] == 0 which indicates no confusion cause at this point in code if that value = 0 then it didn't proceed through 'spec_confuse_wave()' indicating no confusion. [NO CONFUSION]
		
		980 -- confused source has 0 dispersed counts and the confuser source has > 0 dispersed counts in confuser order [YES CONFUSION]

		981 -- confuser source has 0 dispersed counts in the appropriate wavelength range of confused source. [NO CONFUSION]

		985 -- both sources contribute dispersed counts in the region of interest but the ratio (counts_confuser / counts_confused) is less than user specified 'spec_confuse_limit' par. [NO CONFUSION]

		985 -- both sources contribute dispersed counts in the region of interest and the ratio (counts_confuser / counts_confused) is greater than user specified 'spec_confuse_limit' par. [YES CONFUSION]
		
		992 -- confuser source has appropriate geometry to contribute confusing counts but it's 0th order has 0 counts so no confusion [NO CONFUSION]

		995 -- confusion from confuser source has occured OUTSIDE the approrpriate range for the potentially confused source (HEG/MEG cutoff OR OSIP_boundaries ) [NO CONFUSION]

		996 -- confuser from confuser source has occured OUTSIDE the approrpriate range for the confuser source (HEG/MEG cutoff of confuser source) [NO CONFUSION]
		

	#Funtion input:

	spec_conf_arr = spectral confusion dictionary
	src_pos_x_par = array of source X positions for all sources
	subset_arr_par = array of srcIDs for the subset sources.

	"""

	###FLAG DEFINITIONS####
	flag_clean = 'clean'
	flag_warn = 'warn'
	flag_confused = 'confused'

	#text to add to ['flag_comment'] if triggered
	flag_99 = 'no_intersect,'
	flag_995 = ',outside_primary_source_wave_coverage'
	flag_996 = ',outside_confuser_source_wave_coverage'
	flag_992 = ',confuser_has_no_0th_order_counts_triggered_by_order_'
	flag_980 = ',confused_has_0_disp_counts_and_confuser_gtr_0_by_order_'
	flag_981 = ',confuser_has_0_disp_counts_in_order_'
	flag_985 = ',confusion_smaller_than_conf_ratio_by_order_'
	flag_986 = ',confusion_above_conf_ratio_by_order_'

	#######################

	#NOTE-->this function length can be cut in half but I have to be careful how to loop over heg and meg cause the opposite arm is called in each case. This function can be optimized by not calling the counts_circle function for every order.

	#call these once per observation
	skyconverter = Sky2Chandra(fits_list_par)
	evtcrates = read_file(fits_list_par)

	#load the ARF ratio table for all the orders once
	meg_arf_data = read_file(f'{input_dir_par}/MEG_Nth_0th_order_ratios_mkarf.fits')
	heg_arf_data = read_file(f'{input_dir_par}/HEG_Nth_0th_order_ratios_mkarf.fits')

	#Calculate number of counts when determining CONFUSER counts in one order compared to CONFUSED counts in another order.
	def calc_num_counts(ratio_pycrates, order, order_zero_counts, bin_start, bin_end):

		""""
		This will estimate the number of Nth order counts in a spectral arm given a number of 0th order counts in a discrete wavelength range. This information comes from the data file of ARF ratios (Nth_order / 0th_order) calculated from a single HETG on-axis observation. This is to be used as an approximation and will not be exact. If the discrete wavelength range covers several ARF bins then a MEAN of the spectral response bandpass is calculated. Note--> some bandpasses cover big dips in ARF and thus mean may affect results.

		ratio_pycrates = CrissCross fits input table which contains the ratios of responses based on a single on-axis HETG observation. Note, since this takes the ratio of different orders, the buildup of ACIS contamination should not affect this calculation.
		order = the order of the confused source where spectral confusion is believed to occur
		order_zero_counts = the number of 0th order counts of the confused source determined in the wavelength bandpass where spectral confusion occurs. This number will be calculated by counts_circle_band().
		bin_start = the first wavelength in Angstrom where you wish to calculate the average response over
		bin_end = the last wavelength in Angstrom where you wish to calculate the average reponse over

		returns:
			num_counts = An estimation of the number of counts from the confusing source expected to be dispersed into the confused spectral order
			avg_ratio_value = The average spectral response in the bin_start, bin_end bandpass used to estimate num_counts
			
		"""""

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


	#need the keys AND the order numbers in string format
	keys_list = list(spec_conf_arr.keys())
	keys_list.remove('intersect_dist')
	keys_list.remove('xintercept')
	keys_list.remove('yintercept')
	keys_list.remove('flag')
	keys_list.remove('flag_comment')

	
	#This loop sets the flags for when confusion DOES NOT occur. Consider changing in future where default flag value is 'no confusion' and I set when it DOES occur
	for i in range(0,len(src_pos_x_par)):	#loop through each instance of spectral confusion for each source
		for j in range(0, len(src_pos_x_par)):
			for m in keys_list: #one of the keys is 'intersect' so I can't loop through just keys. I need to make sure I'm just looking through the arms (which have subkeys wave and flag)
			
#					if list(spec_conf_arr[m].keys()) == ['wave', 'flag']: #5/3/24 -- note, I removed because I THINK this was older an no longer necessary.
				if spec_conf_arr[m]['wave'][i,j] == 0 or i == j:	#if the spec_conf[arm]['wave'][i,j] value is 0 or if i=j (cant have that confusion) then flag is set to 99 (no intersect)
					#spec_conf_arr[m]['flag'][i,j] = 99
					spec_conf_arr[m]['flag'][i,j] = flag_clean
					spec_conf_arr[m]['flag_comment'][i,j] = flag_99 # dont add on to previous comment cause if there is no intersection then this can be used in loop to only run confusion for intersecting sources
				
		
	#DAVE NOTE --> This sure looks like I can do something to simply switch heg and meg like for w = ['heg', 'meg'] to get rid of half this code! Be careful though cause variable names are different!

	for i in subset_arr_par:	#DAVE NOTE --> changed 10/29/25 -- only loop through subset_arr_par to save cpu time cause unnecessary to run on all sources
		for j in range(0, len(src_pos_x_par)):

			for n in ['-3','-2','-1','+1','+2','+3']:

				if (spec_conf_arr['heg'+n]['flag_comment'][i,j] != flag_99): #dont run counts_circle_band unless there is at least some evidence of confusion - note I am leaving of 999 here cause there could be a case of confusion near the edges where the osip range brings into the real band

					#if the region in the extracted spectrum where confusion occurs is outside the valid wavelength range then flag as warning and continue
					#DAVE NOTE --> I dont think I need to divide by order in this line cause every order's wavelength is determined IN THAT order (not relative to order 1). Every order will have a 1.1 A photon... I think they will also have the same heg/meg cutoff cause it is set by instrument and order 1?
					#DAVE NOTE --> Think about this more! Do I even need to check other orders? The key thing here is I am checking against the wavelengths within each order. Does this issue extend to the OSIP WINDOW CALCULATIONS?

					##KEEP THIS COMMENT--> First check if the intersection between two spectra occur in the possible range of wavelengths for the extracted spectra. If not, it doesn't matter what order or wavelength the other source is, it will NEVER contribute to confusion cause effective area will zero out any flux outside valid range of wave for each source.
					if spec_conf_arr['heg'+n]['wave'][i,j] < (heg_cutoff_low) or spec_conf_arr['heg'+n]['wave'][i,j] > (heg_cutoff_high):
					#if spec_conf_arr['heg'+n]['wave'][i,j] < (heg_cutoff_low/np.abs(int(n))) or spec_conf_arr['heg'+n]['wave'][i,j] > (heg_cutoff_high/np.abs(int(n))):
						spec_conf_arr['heg'+n]['flag'][i,j] = flag_warn
						spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_995	#DAVE consider making this its own unique flag

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

							if spec_conf_arr['meg'+m]['wave'][j,i] != 0 and (spec_conf_arr['meg'+m]['wave'][j,i] < (heg_cutoff_low) or spec_conf_arr['meg'+m]['wave'][j,i] > (heg_cutoff_high)):
								if spec_conf_arr['heg'+n]['flag'][i,j] != flag_confused:
									spec_conf_arr['heg'+n]['flag'][i,j] = flag_warn
								spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] +  flag_996
							
							#if none of the flag_995s trigger that means spectral confusion has occured within the valid ranges of wavelengths anad we need to check counts
							else:

								#START OSIP DETERMINATION FOR EVERY SOURCE with some intersection

								#if CONFUSER source has photons with wavelengths within the OSIP region of the CONFUSED source then run counts_circle_band to determine if confusion can occur. If so, flag. Otherwise, that means there was a potential source of confusion but it was outside OSIP range so it can get a flag of clean if no other orders cause issues. 
								#I was worried if osip_low == 0 then the WRONG arm where no confusion occurs would have its wave[j,i] = 0 and trigger this incorrectly. However 0 is not greater than 0 so just dont change to '>=' and it should be ok.
								
								#if the photons that land in the confused region are within the OSIP bounds then check the number of counts compared to the source counts in that region
								if (spec_conf_arr['meg'+m]['wave'][j,i] > spec_conf_arr['heg'+n]['osip_low'][i,j] and spec_conf_arr['meg'+m]['wave'][j,i] < spec_conf_arr['heg'+n]['osip_high'][i,j]):

									#only run counts_circle_band ONCE per M order cause the 0th order counts dont change
									#run confuser counts first cause if no counts here then all the future calculations are pointless cause no confusion.
									if confuser_0th_counts == [None]:
										confuser_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[j], src_pos_y_par[j], [spec_conf_arr['heg'+n]['osip_low'][i,j],spec_conf_arr['heg'+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in contaminating spectrum at SAME osip window  of confusion

									#if confuser_0th_counts = 0 then we can stop checking the other m orders of the confuser source cause its always the same osip window and if there are no counts in that osip window in the 0th order of the confuser then there wont be confusion in the confused order (ADVANCE n if confuser_0th_counts = 0). It's ok to keep specific m flags cause it will provide knowledge of which m orders had the appropriate osip range.
									if confuser_0th_counts == 0: #could make this number '< 3 or so' if I want to reduce the number of false positives and allow some more cases through to be OK. see code comment above
											
										spec_conf_arr['heg'+n]['flag'][i,j] = flag_warn #confuser has appropriate geometry to contribute confusing counts but it's 0th order has 0 counts	so no confusion				
										spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_992 + m

									#if confuser counts !=0 then I need to run the calculation to determine if dispersed events land in region
									else:
									
										#only run counts_circle_band ONCE per M order cause the 0th order counts dont change
										if confused_0th_counts == [None]:
											confused_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[i], src_pos_y_par[i], [spec_conf_arr['heg'+n]['osip_low'][i,j],spec_conf_arr['heg'+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in the spectrum of interest at osip window of confusion 											

									#if (confuser_counts > 0 and confused_counts > 0):

										#for negative orders mult by -1 so the string is positive 
										if int(n) > 0:
											heg_order = f'p{int(n)}_to_0'
										elif int(n) < 0:
											heg_order = f'm{-1*int(n)}_to_0'

										if int(m) > 0:
											meg_order = f'p{int(m)}_to_0'
										elif int(m) < 0:
											meg_order = f'm{-1*int(m)}_to_0'

										#The estimated number of dispersed counts from the primary (confused) source at the location of the spectral intersection (confusion)
										confused_counts_heg = []
										confused_counts_heg, avg_ratio_heg = calc_num_counts(ratio_pycrates = heg_arf_data, order = heg_order, order_zero_counts =confused_0th_counts, bin_start=spec_conf_arr['heg'+n]['osip_low'][i,j], bin_end = spec_conf_arr['heg'+n]['osip_high'][i,j])

										#The estimated number of dispersed counts from the secondary (confuser) source at the location of the spectral intersection (confusion)
										confuser_counts_meg = []
										confuser_counts_meg, avg_ratio_meg = calc_num_counts(ratio_pycrates = meg_arf_data, order = meg_order, order_zero_counts =confuser_0th_counts, bin_start=spec_conf_arr['heg'+n]['osip_low'][i,j], bin_end = spec_conf_arr['heg'+n]['osip_high'][i,j])

										if (confuser_counts_meg > 0 and confused_counts_heg == 0):
											spec_conf_arr['heg'+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
											spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_980 + m
										
										elif (confuser_counts_meg == 0):
											#DONT OVERWRITE FLAG ONCE IT GETS SET TO CONFUSED
											if spec_conf_arr['heg'+n]['flag'][i,j] != flag_confused:
												spec_conf_arr['heg'+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 
											
											spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_981 + m


										elif (confuser_counts_meg > 0 and confused_counts_heg >0):

											spec_confused_ratio = []
											spec_confused_ratio = (confuser_counts_meg / confused_counts_heg)

											#if the ratio of confusing counts / confused sources counts is higher than some user param then flag as confused
											if spec_confused_ratio > spec_confuse_limit:
												spec_conf_arr['heg'+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
												spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_986 + m													
											else:
												if spec_conf_arr['heg'+n]['flag'][i,j] != flag_confused:
													spec_conf_arr['heg'+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 

												#add warning showing that there is confusion but its lower than some threshold so its ok.
												spec_conf_arr['heg'+n]['flag_comment'][i,j] = spec_conf_arr['heg'+n]['flag_comment'][i,j] + flag_985 + m
												
										else:
											print(f'ERROR --> Something went wrong when determining spectral confusion HEG. i={i},j={j},n={n},m={m}, confused_cnt_heg={confused_counts_heg}, confuser_cnt_meg={confuser_counts_meg}, 0th_ord={confused_0th_counts, confuser_0th_counts}')
											print()

								#dont overwrite 999 but if the source is otherwise outside the OSIP range then its flag is changed to 995. Sources with 999 that ARE within the osip range will have their 999 change in above loop conditions.
								#ASSUMING FLAG WAS PREVIOUSLY 'unset' then mark it as clean if it didn't land in the above loops
								elif spec_conf_arr['heg'+n]['flag'][i,j] != flag_warn and spec_conf_arr['heg'+n]['flag'][i,j] != flag_confused:
									spec_conf_arr['heg'+n]['flag'][i,j] = flag_clean #If it doesnt makes it through the top loop condition then confusion is outside OSIP bounds and should be clean. If it already has A warning or confusion flag then it remains confused and set.



	#########
	# NOW SET MEG FLAGS --SAME logic so should consolidate
	##########
	for i in subset_arr_par:	#DAVE NOTE --> changed 10/29/25 -- only loop through subset_arr_par to save cpu time cause unnecessary to run on all sources
		for j in range(0, len(src_pos_x_par)):

			for n in ['-3','-2','-1','+1','+2','+3']:

				if (spec_conf_arr['meg'+n]['flag_comment'][i,j] != flag_99): #dont run counts_circle_band unless there is at least some evidence of confusion - note I am leaving of 999 here cause there could be a case of confusion near the edges where the osip range brings into the real band

					#if the region in the extracted spectrum where confusion occurs is outside the valid wavelength range then flag as warning and continue
					#DAVE NOTE --> I dont think I need to divide by order in this line cause every order's wavelength is determined IN THAT order (not relative to order 1). Every order will have a 1.1 A photon... I think they will also have the same meg/heg cutoff cause it is set by instrument and order 1?
					#DAVE NOTE --> Think about this more! Do I even need to check other orders? The key thing here is I am checking against the wavelengths within each order. Does this issue extend to the OSIP WINDOW CALCULATIONS?

					##KEEP THIS COMMENT--> First check if the intersection between two spectra occur in the possible range of wavelengths for the extracted spectra. If not, it doesn't matter what order or wavelength the other source is, it will NEVER contribute to confusion cause effective area will zero out any flux outside valid range of wave for each source.
					if spec_conf_arr['meg'+n]['wave'][i,j] < (meg_cutoff_low) or spec_conf_arr['meg'+n]['wave'][i,j] > (meg_cutoff_high):
					#if spec_conf_arr['meg'+n]['wave'][i,j] < (meg_cutoff_low/np.abs(int(n))) or spec_conf_arr['meg'+n]['wave'][i,j] > (meg_cutoff_high/np.abs(int(n))):
						spec_conf_arr['meg'+n]['flag'][i,j] = flag_warn
						spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_995	#DAVE consider making this its own unique flag

					#if the intersection occurs within the valid bounds of the extracted source then check all the orders of the confusing source to see if those are within THEIR respective valid bounds. If they are outside their own bounds then confusion will not occur
					else:

						#set these to NONE HERE so they aren't recalculated needlessly for each confuser order
						confused_0th_counts = [None]
						confuser_0th_counts = [None]
						
						#otherwise (confusion occurs within extracted wavelength range) so check all the orders to see if their contaminating photons occur outside of their respective valid wavelength ranges
						#for m in [1,2,3]:
						#AT this point we know meg and heg arm intersect somewhere within the valid range of the confused (meg) arm. Now we check the valid range of the confuser and if that is valid then do the calculation to see how many spectral counts confuse
						for m in ['-3','-2','-1','+1','+2','+3']:
							#CHECK IF INTERSECTION OCCURS OUTSIDE NORMAL WAVELENGTH BOUNDS FOR meg --> only one of these can be triggered cause only one +/- arm will intersect. meg/heg cutoff should not depend on order cause I am checking within the reference frame of the confuser source. 

							if spec_conf_arr['heg'+m]['wave'][j,i] != 0 and (spec_conf_arr['heg'+m]['wave'][j,i] < (meg_cutoff_low) or spec_conf_arr['heg'+m]['wave'][j,i] > (meg_cutoff_high)):
								if spec_conf_arr['meg'+n]['flag'][i,j] != flag_confused:
									spec_conf_arr['meg'+n]['flag'][i,j] = flag_warn
								spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] +  flag_996
							
							#if none of the flag_995s trigger that means spectral confusion has occured within the valid ranges of wavelengths anad we need to check counts
							else:

								#START OSIP DETERMINATION FOR EVERY SOURCE with some intersection

								#if CONFUSER source has photons with wavelengths within the OSIP region of the CONFUSED source then run counts_circle_band to determine if confusion can occur. If so, flag. Otherwise, that means there was a potential source of confusion but it was outside OSIP range so it can get a flag of clean if no other orders cause issues. 
								#I was worried if osip_low == 0 then the WRONG arm where no confusion occurs would have its wave[j,i] = 0 and trigger this incorrectly. However 0 is not greater than 0 so just dont change to '>=' and it should be ok.
								
								#if the photons that land in the confused region are within the OSIP bounds then check the number of counts compared to the source counts in that region
								if (spec_conf_arr['heg'+m]['wave'][j,i] > spec_conf_arr['meg'+n]['osip_low'][i,j] and spec_conf_arr['heg'+m]['wave'][j,i] < spec_conf_arr['meg'+n]['osip_high'][i,j]):

									#only run counts_circle_band ONCE per M order cause the 0th order counts dont change
									#run confuser counts first cause if no counts here then all the future calculations are pointless cause no confusion.
									if confuser_0th_counts == [None]:
										confuser_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[j], src_pos_y_par[j], [spec_conf_arr['meg'+n]['osip_low'][i,j],spec_conf_arr['meg'+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in contaminating spectrum at SAME osip window  of confusion

									#if confuser_0th_counts = 0 then we can stop checking the other m orders of the confuser source cause its always the same osip window and if there are no counts in that osip window in the 0th order of the confuser then there wont be confusion in the confused order (ADVANCE n if confuser_0th_counts = 0). It's ok to keep specific m flags cause it will provide knowledge of which m orders had the appropriate osip range.
									if confuser_0th_counts == 0: #could make this number '< 3 or so' if I want to reduce the number of false positives and allow some more cases through to be OK. see code comment above
											
										spec_conf_arr['meg'+n]['flag'][i,j] = flag_warn #confuser has appropriate geometry to contribute confusing counts but it's 0th order has 0 counts	so no confusion				
										spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_992 + m

									#if confuser counts !=0 then I need to run the calculation to determine if dispersed events land in region
									else:
									
										#only run counts_circle_band ONCE per M order cause the 0th order counts dont change
										if confused_0th_counts == [None]:
											confused_0th_counts = counts_circle_band(evtcrates, src_pos_x_par[i], src_pos_y_par[i], [spec_conf_arr['meg'+n]['osip_low'][i,j],spec_conf_arr['meg'+n]['osip_high'][i,j]], skyconverter, psffrac=0.9) #num 0th order counts in the spectrum of interest at osip window of confusion 											

									#if (confuser_counts > 0 and confused_counts > 0):


										if int(n) > 0:
											meg_order = f'p{int(n)}_to_0'
										elif int(n) < 0:
											meg_order = f'm{-1*int(n)}_to_0'

										if int(m) > 0:
											heg_order = f'p{int(m)}_to_0'
										elif int(m) < 0:
											heg_order = f'm{-1*int(m)}_to_0'

										#The estimated number of dispersed counts from the primary (confused) source at the lomegion of the spectral intersection (confusion)
										confused_counts_meg = []
										confused_counts_meg, avg_ratio_meg = calc_num_counts(ratio_pycrates = meg_arf_data, order = meg_order, order_zero_counts =confused_0th_counts, bin_start=spec_conf_arr['meg'+n]['osip_low'][i,j], bin_end = spec_conf_arr['meg'+n]['osip_high'][i,j])

										#The estimated number of dispersed counts from the secondary (confuser) source at the lomegion of the spectral intersection (confusion)
										confuser_counts_heg = []
										confuser_counts_heg, avg_ratio_heg = calc_num_counts(ratio_pycrates = heg_arf_data, order = heg_order, order_zero_counts =confuser_0th_counts, bin_start=spec_conf_arr['meg'+n]['osip_low'][i,j], bin_end = spec_conf_arr['meg'+n]['osip_high'][i,j])


										if (confuser_counts_heg > 0 and confused_counts_meg == 0):
											spec_conf_arr['meg'+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
											spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_980 + m
										
										elif (confuser_counts_heg == 0):
											#DONT OVERWRITE FLAG ONCE IT GETS SET TO CONFUSED
											if spec_conf_arr['meg'+n]['flag'][i,j] != flag_confused:
												spec_conf_arr['meg'+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 
											
											spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_981 + m


										elif (confuser_counts_heg > 0 and confused_counts_meg >0):

											spec_confused_ratio = []
											spec_confused_ratio = (confuser_counts_heg / confused_counts_meg)

											#if the ratio of confusing counts / confused sources counts is higher than some user param then flag as confused
											if spec_confused_ratio > spec_confuse_limit:
												spec_conf_arr['meg'+n]['flag'][i,j] = flag_confused #set flag to genuine source of confusion. 
												spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_986 + m													
											else:
												if spec_conf_arr['meg'+n]['flag'][i,j] != flag_confused:
													spec_conf_arr['meg'+n]['flag'][i,j] = flag_warn #set flag to genuine source of confusion. 

												#add warning showing that there is confusion but its lower than some threshold so its ok.
												spec_conf_arr['meg'+n]['flag_comment'][i,j] = spec_conf_arr['meg'+n]['flag_comment'][i,j] + flag_985 + m
												
										else:
											print(f'ERROR --> Something went wrong when determining spectral confusion MEG. i={i},j={j},n={n},m={m}, confused_cnt_meg={confused_counts_meg}, confuser_cnt_heg={confuser_counts_heg}')
											print()								

								#dont overwrite 999 but if the source is otherwise outside teh OSIP range then its flag is changed to 995. Sources with 999 that ARE within the osip range will have their 999 change in above loop conditions.
								#ASSUMING FLAG WAS PREVIOUSLY 'unset' then mark it as clean if it didn't land in the above loops
								elif spec_conf_arr['meg'+n]['flag'][i,j] != flag_warn and spec_conf_arr['meg'+n]['flag'][i,j] != flag_confused:
									spec_conf_arr['meg'+n]['flag'][i,j] = flag_clean #If it doesnt makes it through the top loop condition then confusion is outside OSIP bounds and should be clean. If it already has A warning or confusion flag then it remains confused and set.
	return(spec_conf_arr)




####POINT SOURCE CONFUSION FUNCTIONS####


def pntsrc_dist_to_spec(pntsrc_conf_par, src_pos_x_par, src_pos_y_par, xoff_par, yoff_par, m_arm_par, b_arm_par, arm_ang_par, arm_par):
	""""
	This function calculates perp_dist_to_spec which is the distance in pixels between a confusing 0th order point source and the dipersed spectrum of another source (perpendicular to the spectrum). It also calculates the pntsrc_conf_par['intersect_dist'][arm_par][i,j] variable. NOTE: This calculation should be valid regardless of the roll angle. However, roll angle is used in other functions to determine which orders to fill based on whether 0th order source is 'above' or 'below' the potentially confused grating arm in pixel coords.

	pntsrc_conf_par = point source confusion dictionary to store results
	src_pos_x_par = 0th order x pixel location
	src_pos_y_par = 0th order y pixel location
	xoff_par = x_offset value
	yoff_par = y_offset value
	m_arm_par = heg/meg slope of the grating line on the detector (from y=mx+b and the grating instrumental slope)
	b_arm_par = heg/meg line intercept (from y=mx+b)		
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
				pntsrc_conf_par['intersect_dist'][arm_par][i,j] = abs((src_pos_x_par[j]-src_pos_x_par[i]) / math.sin(math.radians(90-arm_ang_par)) + r0_offset_dist_from_contam_arm[i,j])

	return(pntsrc_conf_par, perp_dist_to_spec_arm, r0_offset_dist_from_contam_arm)




def pntsrc_confuse_wave(pntsrc_conf_par, perp_dist_to_spec_arm_par, src_pos_x_par, P_arm_par, mm_per_pix, X_R, arm_par, roll_nom_par, src_off_axis_par, counts_par, contam_offset_thresh_par, counts_intercept_thresh_i_par, counts_contam_pntsrc_thresh_par):

	"""""
	This function identifies when point source confusion occurs within the thresholds provided by the user. If a 0th order source is sufficiently bright and close to the dispersed spectrum on another source then it will be identified as having point source confusion.  This function uses output from pntsrc_dist_to_spec() with the roll angle to determine where/if point source confusion occurs. NOTE: a single confusing point source can only confuse a single arm for each 'confused' source. So this loop will only flag a single arm for each confused source per confuser source.

	pntsrc_conf_par = point source confusion dictionary to store results
	perp_dist_to_spec_arm_par = output from pntsrc_dist_to_spec() necessary for filtering logic. Needs to match heg/meg arm
	src_pos_x_par = 0th order x pixel location		
	P_arm_par = Period of the heg/meg arm
	mm_per_pix = millimeters per pixel for ACIS (CONSTANT = 0.023987)
	X_R = rowdland diameter in mm constatn (CONSTANT=8632.48)
	arm_par = 'heg' or 'meg'
	roll_nom_par = roll angle of the observation from the fits header
	src_off_axis_par = how far from the pointing (off-axis) a source is
	counts_par = the number of 0th order counts via wavedetect
	contam_offset_thresh_par = [USER PAR] threshold in pixels for how far a point source can be perpendicular from the dispersed spectrum.
	counts_intercept_thresh_i_par = [USER PAR]  threshold to be flagged as a source bright enough to care about if another sources dispersed spectra or another 0th order intersects with it
	
	"""""

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

			if i != j and perp_dist_to_spec_arm_par[i,j] !=0 and (abs(perp_dist_to_spec_arm_par[i,j]) < (contam_offset_thresh_par * off_axis_modifier)) and counts_par[i] > counts_intercept_thresh_i_par and counts_par[j] > counts_contam_pntsrc_thresh_par:
				for m in ['1','2','3']:
					if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
						if src_pos_x_par[j] > src_pos_x_par[i]:
							pntsrc_conf_par[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number
						elif src_pos_x_par[j] < src_pos_x_par[i]:
							pntsrc_conf_par[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number		
						else:
							print(f'ERROR in point source confuse calculation for i,j,m = {i,j,m}')													
					elif (roll_nom_par > 90 and roll_nom_par < 270):
						if src_pos_x_par[j] < src_pos_x_par[i]:
							pntsrc_conf_par[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number
						elif src_pos_x_par[j] > src_pos_x_par[i]:
							pntsrc_conf_par[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (pntsrc_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix )/X_R) ) / int(m), decimals=3) #divide by order number							
						else:
							print(f'ERROR in point source confuse calculation for i,j,m, roll_nom_par = {i,j,m, roll_nom_par}')
					else:
						print('ERROR -- Check roll_nom_par value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')		

	return(pntsrc_conf_par)
						



def pntsrc_confuse_wave_bounds(pntsrc_conf_par, perp_dist_to_spec_arm_par, fits_list_par, subset_arr_par, src_pos_x_par, src_pos_y_par, arm_par,logfile_par, moritz_factor_par=0.1):
	"""""
	This function will run pnt_src_masking_region to determine if the PSF from a potentially confusing point source is sufficient to actually cause confusion. It uses pnt_src_masking_region() which provides a wavelength RANGE to ignore for each spectrum based on the PSF size and energy of the confusing source. What pnt_src_masking_region does is it uses the total number of 0th order counts in the contaminating source and identifies a radius in that source's PSF (which is on the grating arm) where GREATER than that radius, the effect of the contaminating counts is so small we don't care. For example, the PSF has most counts near its center so eventually some of the counts will become much fainter than the spectrum and you can ignore.  This 'radius' is along the grating arm but corresponds to the size of the confusing 0th orders source's PSF. This is why the ignore regions for the point sources are so much smaller than the Spectral arm OSIP crosses. The PSF can be modeled and easily understood as a fraction of the stars counts. Arm crossings are not as easy. So in essence, this boundary is NOT the OSIP range. So the LOW is the lower bound and the high is the upper bound. If the value returned is 9999.0 then that is a flag which indicates the point source does not have any counts in the expected band (and thus isn't confusing the spectrum). I report it this way so users can still see where a point source has landed on their spectrum to double check.

	pntsrc_conf_par = point source confusion dictionary
	fits_list_par = evt2 fits file of the observation
	src_pos_x_par, src_pos_y_par = source x and y positions
	arm_par = 'heg' or 'meg'
	moritz_factor_par = the fraction of events allowed by confuser before considering confusion occurs (0.1 = 10%)
	logfile_par = logfile name 

	"""""

	if arm_par == 'heg':
		tg_part = 1
	elif arm_par == 'meg':
		tg_part = 2
	
	osip = OSIP(fits_list_par)
	skyconverter = Sky2Chandra(fits_list_par)
	evtcrates = read_file(fits_list_par)

	pntsrc_confuse_log_file = open(f'{logfile_par}', 'w')


	for i in subset_arr_par:
		for j in range(0,len(src_pos_x_par)):
			for m in ['-3','-2','-1','+1','+2','+3']:
				if pntsrc_conf_par[arm_par+m]['wave'][i,j] != 0: #only calculate for potential sources of confusion
					pntsrc_conf_par[arm_par+m]['wave_low'][i,j], pntsrc_conf_par[arm_par+m]['wave_high'][i,j] = pnt_src_masking_region( evtcrates, osip, skyconverter, src_pos_x_par[i], src_pos_y_par[i], src_pos_x_par[j], src_pos_y_par[j], np.abs(perp_dist_to_spec_arm_par[i,j]), pntsrc_conf_par[arm_par+m]['wave'][i,j], tg_part, moritz_factor_par, pntsrc_confuse_log_file)

	pntsrc_confuse_log_file.close()

	return(pntsrc_conf_par)





def pntsrc_flag_set(pntsrc_conf_par, src_pos_x_par, arm_par, subset_arr_par, heg_cutoff_low_par = heg_cutoff_low, heg_cutoff_high_par = heg_cutoff_high, meg_cutoff_low_par = meg_cutoff_low, meg_cutoff_high_par = meg_cutoff_high):

	"""""
	Sets the various flags for point source confusion. NOTE--> the flag values already stored in spec_conf['wave'] and ['wave_low']. These are passed to spec_conf when running pntsrc_confuse_wave_bounds() so that is where confusion is actually determined. This function just sets the flags.
	

	Flag Definitions:

	flag_9999 -- The 0th order confusing point source has 0 counts [NO CONFUSION]
	flag_9998 -- The 0th order confusing point source has too few counts to warrant confusion (0th_order_counts_confuser / 0th_order_counts_confused) < 'factor' (~10% default) [NO CONFUSION]
	flag_9997 -- The 0th order confusing point source is relatively weak and too far from spectrum to cause confusion [NO CONFUSION]
	flag_9995 -- The 0th order confusing point source falls outside the valid range of HEG/MEG response bounds [NO CONFUSION]
	flag_9996 -- The 0ther order confusing point source is valid and causes confusion. [YES CONFUSION]

	Note: if the confused spectrum has 0 counts then the entire OSIP range is used for ignoring point source confusion. Otherwise, it is calculated based on fraction of PSF and brightness of confuser source.
	"""""

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
		print('ERROR WRONG ARM PAR USED IN pntsrc_flag_set')

	for i in subset_arr_par:
		for j in range(0,len(src_pos_x_par)):
			for m in ['-3','-2','-1','+1','+2','+3']:

				if pntsrc_conf_par[arm_par+m]['wave'][i,j] == 0:
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_clean

				elif pntsrc_conf_par[arm_par+m]['wave_low'][i,j] == 9999.0:
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_warn
					pntsrc_conf_par[arm_par+m]['flag_comment'][i,j] = flag_9999

				elif (pntsrc_conf_par[arm_par+m]['wave'][i,j] < cutoff_low or pntsrc_conf_par[arm_par+m]['wave'][i,j] > cutoff_high):
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_warn
					pntsrc_conf_par[arm_par+m]['flag_comment'][i,j] = flag_9995

				elif pntsrc_conf_par[arm_par+m]['wave_low'][i,j] == 9998.0:
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_warn
					pntsrc_conf_par[arm_par+m]['flag_comment'][i,j] = flag_9998

				elif pntsrc_conf_par[arm_par+m]['wave_low'][i,j] == 9997.0:
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_warn
					pntsrc_conf_par[arm_par+m]['flag_comment'][i,j] = flag_9997

				else:
					pntsrc_conf_par[arm_par+m]['flag'][i,j] = flag_confused
					pntsrc_conf_par[arm_par+m]['flag_comment'][i,j] = flag_9996				
				


	return(pntsrc_conf_par)




####ARM CONFUSION FUNCTIONS####

def arm_conf_dict(num_sources, highest_order):

	"""""

	This dictionary holds all of the relevant data for arm confusion between two sources. Arm confusion occurs when a confuser source 'j' bright enough to disperse many counts lies on the arm of another source bright enough to disperse many counts. The format of this dictionary is arm_confuse['arm+order'][parameter][i,j] where 'i' is the potentially CONFUSED source and 'j' is the potential CONFUSER source. For example, spec_confuse['meg-1']['wave'][5,10] shows that the meg arm of srcID=5 has potential confusion in the -1 order from the dispersed spectrum of SrcID=10. The value of the 'wave' parameter in this dictionary entry is the wavelength in angstrom where the spectral confusion occurs. Note, this dictionary is similar but slightly different than the point source and spectral confusion.
	
	arm values are 'heg' or 'meg'
	valid arm orders are [-3,-2,-1,+1,+2,+3]

	confusion_dict['intersect_dist'] = The distance in pixels between the 0th order src 'i' and the 0th order src 'j' position (along the arm).
	confusion_dict['0th_cnts_frac'] = the ratio of 0th order counts of the CONFUSER 'i' divided by CONFUSED 'j'
	confusion_dict['arm_confused_wave'] = This identifies which order (e.g., -1 versus +1) the arm confusing 0th order point source lies on. This is used when determinig the range of wavelengths confused in arm confusion.
	
	confusion_dict['flag'] = primary flag which represents potential sources of confusion for ALL orders between source i and j.
	confusion_dict['flag_comment'] = primary flag description which represents potential sources of confusion for ALL orders between source i and j.

	confusion_dict['arm+order']['wave'] = the wavelength where confusion may occur
	confusion_dict['arm+order']['wave_low'] = the lower bounds of where confusion may occur
	confusion_dict['arm+order']['wave_high'] = the upper bounds of where confusion may occur
	confusion_dict['arm+order']['flag'] = the flag which represents potential sources of confusion for a paritcular order between source i and j.
	confusion_dict['arm+order']['flag_comment'] = the flag description which represents potential sources of confusion for a paritcular order between source i and j.		

	"""""

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



def arm_confuse_wave(arm_conf_par, perp_dist_to_spec_arm_par, src_pos_x_par, P_arm_par, arm_par, arm_ang_par, roll_nom_par, src_off_axis_par, r0_offset_dist_from_contam_arm_par, counts_par, subset_arr_par, mm_per_pix_par=mm_per_pix, X_R_par=X_R ):
	
	"""""
	Calculates ratio of 0th order counts (net_counts_confuser / net_counts_confused) for sources with potential arm confusion. This parameter is used in loop logic to flag arm confusion but also printed to final table to allow users judgement in determining if they want to remove associated confusion or not. 

	Calculates the distance from the 0th order confused source (wavelength) where the 0th order of the confuser falls on the spectrum. This distance (dx) is then used in later calculations to determine the wavelenght bounds where arm confusion can occur.

	Many of the arm conf pars are the same as point source confusion since arm confusion occurs when a (bright) 0th order point sources falls on the spectrum of a source of interest. 

	arm_conf_par = arm_conf dictionary
	perp_dist_to_spec_par = distance in pixels from the 0th order confusing source (j) perpendicular to the dispersed arm of the confused source (i)
	src_post_x_par = array of source positions
	arm_par = 'heg' or 'meg'
	arm_ang_par = grating angle unique for meg and heg
	roll_nom_par = roll angle of the observation
	r0_offset_dist_from_contam_arm_par = (defined previously) This is an offset value needed when calculating the distance between 0th order of the confused source and the 0th order of the confuser source.
	counts_par = array of 0th order counts for each source

	Note --> arm confusion is calcualted using an off_axis_modifier which is an ESTIMATE of how the off-axis angle of the confuser source may impact arm confusion due to its larger PSF size. This is separated into three spatial bins of < 3' (arcmin), > 3' and < 6' and > 6' using Fig 4.13 of the Chandra proposers observing guide which shows the HRMA encircled energy fraction for off-axis sources. Focusing on the 1.5 keV curve,  if a 1'' PSF is 2pix up and 2pix down (4pix but confusing source also has 4pix so equals 8pix then + 2 just in case = 10 = dist_to_super_bright_perp) then I can *assume* the number of pixels = 4*the eef. So at 2'' its off axis angle of 4' so then its 4pix*2+2 * 2 and so on and so on. Should be ok cause most sources at least [i] will be < 3' but there may be issues for far off-axis sources espcially if they also intersect with other far off-axis sources. 

	"""""


	for i in subset_arr_par:

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
			if i != j and counts_par[i] > 0 and counts_par[j] > min_HETG_counts and np.abs(perp_dist_to_spec_arm_par[i,j]) < (dist_to_super_bright_perp * off_axis_modifier_i * off_axis_modifier_j):
				arm_conf_par['0th_cnts_frac'][arm_par][i,j] = counts_par[j] / counts_par[i]

			#second, use '0th_cnts_frac' to calcualte arm_confusion location -- Basically identical to point source confusion calculation but with different loop condition.
			if (perp_dist_to_spec_arm_par[i,j] != 0) and (arm_conf_par['0th_cnts_frac'][arm_par][i,j] > 0):
				arm_conf_par['intersect_dist'][arm_par][i,j] = abs((src_pos_x_par[j]-src_pos_x_par[i]) / math.sin(math.radians(90-arm_ang_par)) + r0_offset_dist_from_contam_arm_par[i,j])

				for m in ['1','2','3']:
					if (roll_nom_par > 271 and roll_nom_par < 360) or (roll_nom_par >0 and roll_nom_par < 90):
						if src_pos_x_par[j] > src_pos_x_par[i]:
							arm_conf_par[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number
						elif src_pos_x_par[j] < src_pos_x_par[i]:
							arm_conf_par[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number		
						else:
							print(f'ERROR in point source confuse calculation for i,j,m = {i,j,m}')													
					elif (roll_nom_par > 90 and roll_nom_par < 270):
						if src_pos_x_par[j] < src_pos_x_par[i]:
							arm_conf_par[arm_par+'+'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number
						elif src_pos_x_par[j] > src_pos_x_par[i]:
							arm_conf_par[arm_par+'-'+m]['wave'][i,j] = np.around(( P_arm_par * ( (arm_conf_par['intersect_dist'][arm_par][i,j]*mm_per_pix_par )/X_R_par) ) / int(m), decimals=3) #divide by order number							
						else:
							print(f'ERROR in point source confuse calculation for i,j,m, roll_nom_par = {i,j,m, roll_nom_par}')
					else:
						print('ERROR -- Check roll_nom_par value and make sure it isnt close to 90 or 270, if so plus and minus orders may be confused')


	return(arm_conf_par)



def determine_confused_order(arm_conf_par, src_pos_x_par, arm_par):

	"""""
	Identifies which of the arm orders that the 0th order lands on for later use in arm boundary calculation (dx). Note, for an i,j pair there can only be ONE arm+order the 0th order falls on. 

	arm_conf_par = arm confusion dictionary
	src_pos_x_par = src X positions
	arm_par = 'heg' or 'meg'

	"""""

	for i in range(len(src_pos_x_par)):
		for j in range(len(src_pos_x_par)):
			if arm_conf_par['0th_cnts_frac'][arm_par][i,j] > 0:
				if arm_conf_par[arm_par+'+1']['wave'][i,j] != 0:	#note, change to easily demonstrate that !=0 means the value is filled and that is then where the confusion occurs between this and negative order. heg+1 and -1 can't both be filled for same source.
					arm_conf_par['arm_confused_wave'][arm_par][i,j] = arm_conf_par[arm_par+'+1']['wave'][i,j]
				elif arm_conf_par[arm_par+'-1']['wave'][i,j] != 0:
					arm_conf_par['arm_confused_wave'][arm_par][i,j] = -1 * arm_conf_par[arm_par+'-1']['wave'][i,j]  # make the negative order negative
				
	return(arm_conf_par)



def calc_ccd_energy_res(arm_par):
	
	"""""
	Creates an array of resolving power as a function of wavelength for MEG and HEG. Matches a polynomial fit of the ACIS resolving power as a function of energy (fig 6.14 in the proposers obseravtory guide) to the HEG/MEG arms for use in arm_flag_set() when calculating the OSIP boundaries for two sources that suffer arm confusion.
	"""""

	if arm_par == 'heg' or arm_par == 'HEG':
		max_wave = 16 #must be int
		res_element = 0.01
	elif arm_par == 'meg' or arm_par == 'MEG':
		max_wave = 32 #must be int
		res_element = 0.02


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



def arm_flag_set(arm_conf_par, arm_par, src_pos_x_par, res_power_arm_maxed_par, hetg_arr_arm_par, subset_arr_par, nsig_par=6, heg_cutoff_high_par = heg_cutoff_high, meg_cutoff_high_par = meg_cutoff_high):

	"""""
	When arm confusion occurs, order sorting regions will overlap depending on the distance between the two 0th order point sources (dx). This will calculate the wavelength for each order where the dispersed counts of a confuser source will improperly be assigned to the extracted (confused) source. These calculated wavelenghts are saved to ['wave_low'] and ['wave_high'] for each source and the flags are set appropriately (as described below).

	Flags:

	flag_99 = 'arm is confused from another bright source'
	flag_98 = 'only one of the two +/- orders of an arm is confused because the confuser source distance (dx) is sufficiently large to allow order sorting to mitigate confusion on the other arm'
	"""""

	flag_clean = 'clean'
	flag_warn = 'warn'
	flag_confused = 'confused'

	flag_99 = 'arm_confusion'
	flag_98 = 'opposite order has arm confusion'

	if arm_par == 'heg' or arm_par == 'HEG':
		arm_cutoff_high = heg_cutoff_high_par
	elif arm_par == 'meg' or arm_par == 'MEG':
		arm_cutoff_high = meg_cutoff_high_par



	for i in subset_arr_par:
		for j in range(0,len(src_pos_x_par)):

			if arm_conf_par['arm_confused_wave'][arm_par][i,j] != 0:

				arm_confuse_hetg = [None] * len(hetg_arr_arm_par)
				x = hetg_arr_arm_par
				dx = arm_conf_par['arm_confused_wave'][arm_par][i,j]
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
	# 								print('sigma = %s' % nsig)
	# 								print('\nsorted bad_arm index value = %s' % (bad_arm[0][z]+1))
	# 								print('sorted bad_arm index value = %s' % bad_arm[0][z+1])
	# 								print('good arm_confuse_value = %s' % arm_confuse_hetg1[bad_arm[0][z]+1])
	# 								print('good arm_confuse_value = %s' % arm_confuse_hetg1[bad_arm[0][z+1]-1])
	# 								print('spectrum is good >= %s' % hetg_arr_HEG[bad_arm[0][z]+1])
	# 								print('spectrum is good <= %s' % hetg_arr_HEG[bad_arm[0][z+1] -1 ])
							if dx > 0:		
								hetg_element_low = bad_arm[0][z]+1
								hetg_element_high = bad_arm[0][z+1]
	# 								print('sigma = %s' % nsig)
	# 								print('\nsorted bad_arm index value = %s' % (bad_arm[0][z]+1))
	# 								print('sorted bad_arm index value = %s' % bad_arm[0][z+1])
	# 								print('good arm_confuse_value = %s' % arm_confuse_hetg1[bad_arm[0][z]+1])
	# 								print('good arm_confuse_value = %s' % arm_confuse_hetg1[bad_arm[0][z+1]-1])
	# 								print('spectrum is good >= %s' % hetg_arr_HEG[bad_arm[0][z]+1])
	# 								print('spectrum is good <= %s' % hetg_arr_HEG[bad_arm[0][z+1] -1 ])
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
					arm_conf_par[arm_par+'+'+m]['wave_low'][i,j] = hetg_high / int(m)
					arm_conf_par[arm_par+'+'+m]['wave_high'][i,j] = arm_cutoff_high / int(m)
					
					#negative orders
					arm_conf_par[arm_par+'-'+m]['wave_low'][i,j] = np.abs(hetg_low) / int(m)
					arm_conf_par[arm_par+'-'+m]['wave_high'][i,j] = arm_cutoff_high / int(m)

					#if both values are pegged at limits then no confusion, otherwise one or both orders are confused.
					if (hetg_low == (-1*arm_cutoff_high) and hetg_high == (-1*arm_cutoff_high)):
						arm_conf_par[arm_par+'+'+m]['flag'][i,j] = flag_clean

						arm_conf_par[arm_par+'-'+m]['flag'][i,j] = flag_clean

					elif (hetg_low == (-1*arm_cutoff_high)):

						arm_conf_par[arm_par+'-'+m]['flag'][i,j] = flag_warn
						arm_conf_par[arm_par+'-'+m]['flag_comment'][i,j] = flag_98
						
						arm_conf_par[arm_par+'+'+m]['flag'][i,j] = flag_confused
						arm_conf_par[arm_par+'+'+m]['flag_comment'][i,j] = flag_99

					elif (hetg_high == (-1*arm_cutoff_high)):

						arm_conf_par[arm_par+'-'+m]['flag'][i,j] = flag_confused
						arm_conf_par[arm_par+'-'+m]['flag_comment'][i,j] = flag_99
						
						arm_conf_par[arm_par+'+'+m]['flag'][i,j] = flag_warn
						arm_conf_par[arm_par+'+'+m]['flag_comment'][i,j] = flag_98

					else:
						arm_conf_par[arm_par+'+'+m]['flag'][i,j] = flag_confused
						arm_conf_par[arm_par+'+'+m]['flag_comment'][i,j] = flag_99

						arm_conf_par[arm_par+'-'+m]['flag'][i,j] = flag_confused
						arm_conf_par[arm_par+'-'+m]['flag_comment'][i,j] = flag_99										


	return(arm_conf_par)


####MAIN FLAG SET####


def main_flag_set(conf_dict_par, src_pos_x_par, subset_arr_par):
	"""""
	This will set the main flag parameters (spec, pntsrc, arm)_conf['flag'] and ['flag_comment'] values based on their respective ['arm+order']['flag'] values. If one source [i] has no confusion with another source [j] based on the individual flags, then the entire source will be determined 'clean' (no confusion). If ALL arm+order flags are either 'clean' or 'warn' then this will set flag to 'warn'. If ANY arm+order flag is 'confused' then this value will become 'confused'. This is primarily used in write_conf_table() to remove unnecessary output.

	#note, the order of the 'else-ifs' in this loop are important. Clean flag is only set if 'confused' or 'warn' doesn't trigger first.
	#consider redoing this flag in a way that doesn't have to loop through so many things.
	"""""

	#for i in range(0,len(src_pos_x)):
	for i in subset_arr_par:
		for j in range(0,len(src_pos_x_par)):
			flag_checker = np.array([], dtype='object')
			flag_warn_comments = ''
			flag_confused_comments = ''				
			# flag_warn_comments = np.array([], dtype='object')
			# flag_confused_comments = np.array([], dtype='object')

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
				



def write_full_conf_table(spec_conf_par, pntsrc_conf_par, arm_conf_par, obsid_par, working_dir_par, srcID_par, counts_par ,remove_clean = 'yes', row_num=808, consolidate_table = False):

	"""""
	Extracts a single source (row) from the three nested dictionaries (one for each confusion type) and creates a fits table summarizing the detected confusion parameters. The user has the option of saving every source and their associated parameter values but most of the time there is no confusion and its unneccesary to include everything. Users can filter to only produce tables where confusion occurs (flag='confused') or where confusion was close to occuring (flag='warn'). This is a relatively complex function to accomodate pycrates as a fits-writing tool throughout CrissCross. This function could be made significantly simpler using astropy or pandas tables.
	
	spec_conf_par = spec confusion dictionary
	pntsrc_conf_par = point source confusion dictionary
	arm_conf_par = arm confusion dictionary
	obsid_par = observation ID
	remove_clean = 'yes' -- will only save flag='confused' or flag='warn' instances of confusion to the output table. 'no' -- will save ALL instances (including flag = 'clean')
	row_num = The element of the input source list for which you want to create a confusion table. 
	srcID_par = the array of srcIDs to save into confusion tables
	counts_par = counts array holding the 0th order counts for each source in source list.
	consolidate_table = 'yes' -- Generate a consolidated table where every row shows a single instance of confusion. This table is most helpful for using with spectral fitting/plotting programs.
	"""""


	def set_mask_par(spec_conf_par, pntsrc_conf_par, arm_conf_par, remove_clean, row_num ):
		"""""
		Sets the mask parameter which identifies the table rows to include in the final output product. If 'remove_clean' = 'yes' then the output tables will only show sources that have at least one flag=confused or flag=warn in all of the arms/orders/confusion_type. If 'remove_clean' != 'yes' then all sources are included in the final table. Warning -- if the number of sources are large then this table can become large fast. 
		"""""
		
		if remove_clean == 'yes':
			mask_par = np.where( ((spec_conf_par['flag'][row_num] == 'confused') | (spec_conf_par['flag'][row_num] == 'warn')) | ((pntsrc_conf_par['flag'][row_num] == 'confused') | (pntsrc_conf_par['flag'][row_num] == 'warn')) | ((arm_conf_par['flag'][row_num] == 'confused') | (arm_conf_par['flag'][row_num] == 'warn'))    )[0].tolist()

		else:
			mask_par = None

		return(mask_par)



	def extract_conf_row(confusion_dict, row_index, mask_par):
		"""
		Extracts a single row from every array inside the confusion_dict
		and returns a new nested dictionary with the same structure. This utilizes that mask_parameter from set_mask_par() and will only return the indices included in the mask (if remove_clean = 'yes').
		"""

		filtered_dict = {}

		for key, value in confusion_dict.items():

			# Case 1: arm+order keys (dict of arrays)
			if isinstance(value, dict) and all(isinstance(v, np.ndarray) for v in value.values()):
				filtered_dict[key] = {}
				for subkey, arr in value.items():
					if mask_par != None:
						filtered_dict[key][subkey] = arr[row_index, mask_par]
					else:
						filtered_dict[key][subkey] = arr[row_index, :]


			# Case 2: intersect_dist, xintercept, yintercept (dict of heg/meg arrays)
			elif isinstance(value, dict) and set(value.keys()) == {"heg", "meg"}:
				if mask_par != None:
					filtered_dict[key] = {
						"heg": value["heg"][row_index, mask_par],
						"meg": value["meg"][row_index, mask_par]
					}
				else:
					filtered_dict[key] = {
						"heg": value["heg"][row_index, :],
						"meg": value["meg"][row_index, :]
					}						

			# Case 3: global arrays (flag, flag_comment)
			elif isinstance(value, np.ndarray):
				if mask_par != None:
					filtered_dict[key] = value[row_index, mask_par]
				else:
					filtered_dict[key] = value[row_index, :]
					
			else:
				raise ValueError(f"Unexpected structure in key '{key}'")

		return(filtered_dict)



	def flatten_confusion_dict(d, parent_key="", sep="_"):
		
		"""""
		crates wont take a nested dictionary as an argument so this flattens the dictionary for easy input to crates.
		"""""

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
		
		"""""
		Crates won't accept 'object' datatypes (the flags and flag_comments in the dictionary) so this converts them to strings.
		"""""

		for i in flat:
			if flat[i].dtype == 'O':
				flat[i] = flat[i].astype(str)

		return(flat)


	def merge_conf_crates(conf_crate_par, merged_crate_par):

		"""""
		Concatenates crate tables (conf_crate_par) to a new 'merged' table. This is used to concatenate the multiple types of confusion (spec, pntsrc and arm) since they are all (mostly) unique.
		"""""

		for colname in conf_crate_par.get_colnames():
			col = conf_crate_par.get_column(colname)
			merged_crate_par.add_column(col)

		return(merged_crate_par)



	def make_flattened_conf_table(conf_par, root_par, mask_par):

		"""""
		Runs several of the above functions to ultimately create a crates table from a nested dictionary while appending the name of the dictionary (spec, pnt, arm) to the columns. Returns crate for table generation and flattened dict for use in consolidated table.
		"""""
	
		single_row = extract_conf_row(conf_par, row_num, mask_par)
		flattened_dict = flatten_confusion_dict(single_row)
		flattened_dict = convert_obj_to_string(flattened_dict)
		flattened_dict = { root_par + key: value for key, value in flattened_dict.items() }


		crate_conf = make_table_crate(flattened_dict)

		return(crate_conf, flattened_dict)


	def make_ancillary_crate(srcID_par, counts_par, mask_par, spec_conf_par, obsid_par):
		"""""
		Add supplementary info to the table such as obsID, srcID and number of 0th order counts before merging all three sources of confusion. 
		"""""

		obsid_arr = CrateData()
		srcid_arr = CrateData()
		pntsrc_counts_arr = CrateData()

		obsid_arr.name = 'obsID'
		srcid_arr.name = 'confuser_srcID'
		pntsrc_counts_arr.name = '0th_order_confused_cnts'


		if mask_par == None:
			num_sources = len(spec_conf_par['flag'])
			
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

	mask_par = set_mask_par(spec_conf_par, pntsrc_conf_par, arm_conf_par, remove_clean, row_num)
	# print(mask_par)
	# print(type(mask_par))
	# print(len(mask_par))

	spec_conf_crate, spec_conf_flattened = make_flattened_conf_table(conf_par=spec_conf_par, root_par='spec_', mask_par = mask_par)
	pntsrc_conf_crate, pntsrc_conf_flattened =  make_flattened_conf_table(conf_par=pntsrc_conf_par, root_par='pnt_', mask_par = mask_par)
	arm_conf_crate, arm_conf_flattened =  make_flattened_conf_table(conf_par=arm_conf_par, root_par = 'arm_', mask_par = mask_par)

	ancillary_crate = make_ancillary_crate(srcID_par=srcID_par, counts_par=counts_par, mask_par=mask_par, spec_conf_par=spec_conf_par, obsid_par=obsid_par)

	merged_crate = TABLECrate()
	
	merged_crate = merge_conf_crates(conf_crate_par = ancillary_crate, merged_crate_par = merged_crate)
	merged_crate = merge_conf_crates(conf_crate_par = spec_conf_crate, merged_crate_par = merged_crate)
	merged_crate = merge_conf_crates(conf_crate_par = pntsrc_conf_crate, merged_crate_par = merged_crate)
	merged_crate = merge_conf_crates(conf_crate_par = arm_conf_crate, merged_crate_par = merged_crate)


	write_file(merged_crate, f'{working_dir_par}/confused_src_{row_num}_full_obsID_{obsid_par}.fits', clobber=True)

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

		write_file(consolidated_crate, f'{working_dir_par}/confused_src_{row_num}_consolidated_obsID_{obsid_par}.fits', clobber=True)


	#return(merged_crate)
	return()



def end_of_run_cleanup(output_dir_list_par, obsid_par, working_dir_par):
	"""""
	Cleans up directory at end of CrissCross run
	"""""

	os.system('mkdir -p %s/confusion_output_files' %output_dir_list_par)
			
	# os.system('mkdir -p %s/confusion_output_files/spectral_contamination' %(output_dir_list_par))
	# os.system('mkdir -p %s/confusion_output_files/point_source_contamination' %output_dir_list_par)
	# os.system('mkdir -p %s/confusion_output_files/source_contamination_dont_use_these' %output_dir_list_par)
	os.system('mkdir -p %s/confusion_output_files/table_fits_data' %output_dir_list_par) #added to hold the fits tables



	# So now this will delete EVERYTHING *.txt in these directories BEFORE the new files get moved there from the working dir
	old_files_spec_contam=sorted(glob.glob('%s/confusion_output_files/spectral_contamination/*.txt' % output_dir_list_par)) #BUG from earlier, the [0] in output_dir_list_par was missing and it wasnt deleting all the old files before saving new ones
	for i in range(len(old_files_spec_contam)):
		os.remove(old_files_spec_contam[i])
	
	old_files_pnt_contam=sorted(glob.glob('%s/confusion_output_files/point_source_contamination/*.txt' % output_dir_list_par))
	for i in range(len(old_files_pnt_contam)):
		os.remove(old_files_pnt_contam[i])

	old_files_src_contam=sorted(glob.glob('%s/confusion_output_files/source_contamination_dont_use_these/*.txt' % output_dir_list_par))
	for i in range(len(old_files_src_contam)):
		os.remove(old_files_src_contam[i])

	old_files_fits_table=sorted(glob.glob('%s/confusion_output_files/table_fits_data/*.fits' % output_dir_list_par))
	for i in range(len(old_files_fits_table)):
		os.remove(old_files_fits_table[i])


	output_table_full=sorted(glob.glob(working_dir_par+'/confused_src_*full*.fits'))
	output_table_consolidated=sorted(glob.glob(working_dir_par+'/confused_src_*consolidated*.fits'))

	#loops to delete a file if it is in the glob list and has a size of zero bytes (meaning the code didn't find any confusion in that source so no reason to pollute your directory)

	for i in range(len(output_table_full)):
		file_size_table=os.stat(output_table_full[i])
		if file_size_table.st_size == 46080: #note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the number of columns!
			os.remove('%s' %output_table_full[i])

	for i in range(len(output_table_consolidated)):
		file_size_table=os.stat(output_table_consolidated[i])
		if file_size_table.st_size == 5760: #note, this filesize is for the 'empty' fits but it is likely to change since I will probably change the number of columns!
			os.remove('%s' %output_table_consolidated[i])


	#now I am moving the reminaing files with filesize > 0 bytes to their respective directores.

	files_to_move = glob.glob(f'{working_dir_par}/confused_src*{obsid_par}.fits')
	for i in files_to_move:
		shutil.move(i, f'{output_dir_list_par}/confusion_output_files/table_fits_data')



	#now we also move the original source list per obsid as well as the wavedetect region file and pnt_src logfile to the output directory for housekeeping. Can use mv since small number of files.
	subprocess.call("mv src_list_%s.txt %s" %(obsid_par, output_dir_list_par), shell=True)
	subprocess.call("mv pnt_src_confuse_%s_log.txt %s" %(obsid_par, output_dir_list_par), shell=True)
	subprocess.call("mv spec_confuse_%s_log.txt %s" %(obsid_par, output_dir_list_par), shell=True)
	#subprocess.call("mv wave_source_list_%s.reg %s" %(obsid_par, output_dir_list_par), shell=True)
	#subprocess.call("mv confuser_souce_list_%s.reg %s" %(obsid_par, output_dir_list_par), shell=True)


	return()


def time_logger(mode, time_started=[], time_counter=[], message=[]):
	"""""
	Creates a time logger and prints relevant steps in the code to the screen. 

	Example usage:

	time_log_start, time_log_counter = time_logger(mode='start')
	time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message='message 1')
	time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message='message 2')

	"""""

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
		print('something went wrong')
		
	return()


def clean_spec(cc_table, pha_file, arf_file, src_num):

	

	"""""
	Takes the confusion table for a source and zeros out the portion of the spectrum where confusion occurs.
	"""""

	def convert_order(order_int):
		"""
		takes an integer and converts it to a string with a + or - sign in front of it (for compatibility with CrissCross cleaning table)
		"""
		if order_int > 0:
			return(f'+{order_int}')
		elif order_int < 0:
			return(f'-{-1*order_int}')
		else:
			print('ERROR, 0th order is included and that is not compatible with clean_spec')

	def convert_arm(tg_part_val):
		"""
		takes the tg_part value and converts it to 'heg' or 'meg' (for compatibility with CrissCross cleaning table)
		"""

		if tg_part_val == 1:
			return('heg')
		elif tg_part == 2:
			return('meg')
		else:
			print(f'ERROR, arm cannot be identified')


	def clean_data(cc_table, pha_crate, arf_data_var, pha_arm_var, pha_order_var, pha_element, conf_flag_var = 'confused'):
		"""
		Docstring for clean_data
		"""
		cc_data = read_file(cc_table)
		pha_data_var = pha_crate.get_crate(2)


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
			specresp_arr = arf_data_var.SPECRESP.values[pha_element]
			fracexpo_arr = arf_data_var.FRACEXPO.values[pha_element]
			bin_low_arr = pha_data_var.BIN_LO.values[pha_element]
			bin_high_arr = pha_data_var.BIN_HI.values[pha_element]	

		else:
			print('ERROR -- PHA datatype must be 1 or 2')
			return()		


		#copies the counts column of the PHA file for modification
		cleaned_spec_var = counts_arr.copy()
		cleaned_staterr_var = stat_err_arr.copy()

		#copies the SPECRESP and fracexpo columns from the arf
		cleaned_specresp_var = specresp_arr.copy()
		cleaned_fracexpo_var = fracexpo_arr.copy()


		for i in range(0,len(cc_data.wave_low.values)):
			if cc_data.flag.values[i] == conf_flag_var and cc_data.grating_type.values[i] == pha_arm_var and cc_data.order.values[i] == pha_order_var:
				elements_to_clean = np.where( (bin_low_arr >= cc_data.wave_low.values[i]) & (bin_high_arr <= cc_data.wave_high.values[i]) ) #identify elements
				
				#clean PHA (spectrum)
				cleaned_spec_var[elements_to_clean] = 0. #set elements that overlap to zero
				cleaned_staterr_var[elements_to_clean] = 1.86603 #double check that this makes sense and the stat_err is always this value for zero counts. I suspect instead I should take min of this column and set it to that.

				#clean ARF
				cleaned_specresp_var[elements_to_clean] = 0.
				cleaned_fracexpo_var[elements_to_clean] = 0.

		return(cleaned_spec_var, cleaned_staterr_var, cleaned_specresp_var, cleaned_fracexpo_var)



	pha_crate_dataset = read_pha(pha_file) #use read_pha cause it brings along all the neccessary extensions
	
	if is_pha_type1(pha_crate_dataset):

		pha_data = pha_crate_dataset.get_crate(2) #extension 2 contains the PHA data
		arf_data = read_file(arf_file)

		#determine the heg/meg arm and order and obsid
		tg_part = get_keyval(pha_data, 'TG_PART') #tg_part = 1 = heg; tg_part = 2 = meg
		tg_m = get_keyval(pha_data, 'TG_M')
		tg_obs = get_keyval(pha_data, 'OBS_ID')
		tg_obs_arf = get_keyval(arf_data, 'OBS_ID')

		#check to make sure obsID of arf and pha file are the same. 
		if tg_obs != tg_obs_arf:
			print('ERROR -- PHA file and ARF are not from same obsID')
			return()

		#setup tgpart and order to be consistent with values in confusion tables.
		pha_arm = convert_arm(tg_part)
		pha_order = convert_order(tg_m)

		cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(cc_table = cc_table, pha_crate = pha_crate_dataset, arf_data_var = arf_data, pha_arm_var = pha_arm, pha_order_var = pha_order, pha_element=0, conf_flag_var = 'confused')

		#replaces the original arrays with the new arrays
		pha_data.COUNTS.values = cleaned_spec
		pha_data.STAT_ERR.values = cleaned_staterr
		arf_data.SPECRESP.values = cleaned_specresp
		arf_data.FRACEXPO.values = cleaned_fracexpo

		#appends the original files to the history for record keeping
		pha_data.add_record("HISTORY", f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ")
		arf_data.add_record("HISTORY", f"This cleaned ARF was created using the ARF file: {arf_file} and the CrissCross cleaning table: {cc_table}. ")

		update_crate_checksum(pha_data)
		update_crate_checksum(arf_data)

		#saves file while maintaining the original header.
		write_pha(pha_crate_dataset, f'src_{src_num}_obsid_{tg_obs}_{pha_arm}_{pha_order}_cleaned.pha', clobber=True)
		write_file(arf_data, f'src_{src_num}_obsid_{tg_obs}_{pha_arm}_{pha_order}_cleaned.arf', clobber=True)


	#PHA2 files need to be treated a little different because they are arrays of arrays and order/arm info is not in header
	elif is_pha_type2(pha_crate_dataset):
		
		arf_data_arr = np.zeros(len(arf_file), dtype='object') # create an array to hold the N arfs (one for each order)
		for i in range(0,len(arf_file)):
			arf_data_arr[i] = read_file(arf_file[i])

		pha_data_full = pha_crate_dataset.get_crate(2)
		
		#check to make sure there are 12 orders (for HETG data)
		if np.shape(pha_data_full.COUNTS.values[0]) != 12:
			print('ERROR -- PHA 2 file does not have all 12 HEG/MEG orders. Consider running clean_spec() on individual pha1 order files or a complete PHA 2 file')
			return()

		tg_m_arr = pha_data_full.TG_M.values
		tg_part_arr = pha_data_full.TG_PART.values

		pha_order_arr = []
		for i in tg_m_arr:
			pha_order_arr.append(convert_order(order_int=i))

		pha_arm_arr = []
		for i in tg_part_arr:
			pha_arm_arr.append(convert_arm(tg_part_val=i))


		#run for every arm and order
		for i in range(0,12):
			
			cleaned_spec, cleaned_staterr, cleaned_specresp, cleaned_fracexpo = clean_data(cc_table = cc_table, pha_crate = pha_crate_dataset, arf_data_var = arf_data[i], pha_arm_var = pha_arm_arr[i], pha_order_var = pha_order_arr[i], pha_element = i, conf_flag_var = 'confused')

			#replaces the original arrays with the new arrays
			pha_data.COUNTS.values[i] = cleaned_spec
			pha_data.STAT_ERR.values[i] = cleaned_staterr
			arf_data_arr[i].SPECRESP.values = cleaned_specresp
			arf_data_arr[i].FRACEXPO.values = cleaned_fracexpo

			arf_data_arr[i].add_record("HISTORY", f"This cleaned ARF was created using the ARF file: {arf_file[i]} and the CrissCross cleaning table: {cc_table}. ")
			update_crate_checksum(arf_data_arr[i])
			write_file(arf_data_arr[i], f'src_{src_num}_obsid_{tg_obs}_{pha_arm_arr}_{pha_order_arr}_cleaned.arf', clobber=True)


		#appends the original files to the history for record keeping
		pha_data_full.add_record("HISTORY", f"This cleaned spectrum was created using the PHA file: {pha_file} and the CrissCross cleaning table: {cc_table}. ")

		update_crate_checksum(pha_data_full)

		#saves file while maintaining the original header.
		write_pha(pha_crate_dataset, f'src_{src_num}_obsid_{tg_obs}_{pha_arm_arr}_{pha_order_arr}_cleaned.pha', clobber=True)


	else:
		print('ERROR -- input PHA file was not a PHA1 or PHA2 type file')

	#return(pha_data, arf_data)	
	return()	

####TESTING
src = 449
obs = 8589
test_spec_dir = 'input_files/testing/hetg_spectra'
pha_data, arf_data = clean_spec(cc_table = f'{test_spec_dir}/confused_src_{src}_consolidated_obsID_{obs}.fits', pha_file = f'{test_spec_dir}/src_449_obsid_8589_repro_meg_p1.pha', arf_file = f'{test_spec_dir}/src_449_obsid_8589_repro_meg_p1.arf', src_num = src)



def find_hetg_pipeline_resp(pha2_file, resp_dir=None):
	from pathlib import Path
	from pycrates import get_history_records

	pha2_dataset = read_pha(pha2_file)
	spec_crate = pha2_dataset.get_crate(2)

	#There are two primary ways to get HETG data via simple commands (maybe three if you count downloading manually from tgcat). (1) download an HETG observation from  either chaser or 'download_chandra_obsid' which gives you the archive (DS-reduced) file structure (e.g., response folder). (2) Running chandra_repro on (1) to get a CIAO produced file structure (e.g., tg folder). Users can also rename the spectral files with the 'root' keyword in chandra_repro.

	creator_key = get_keyval(spec_crate, 'CREATOR')
	
	if 'Version DS' in creator_key:
		#if users pha2_file is a long path or a single file, strip the name and check for the root so the arf glob doesn't get any extra unrelated files in the response dir
		pha_name = Path(pha2_file).name
		pha_root = pha_name.partition('_pha2.fits')[0]
		if resp_dir == None:
			arf_list = glob.glob(f'responses/{pha_root}*arf2.fits*')
			rmf_list = glob.glob(f'responses/{pha_root}*rmf2.fits*')
		else:
			arf_list = glob.glob(f'{resp_dir}/{pha_root}*arf2.fits*')
			rmf_list = glob.glob(f'{resp_dir}/{pha_root}*rmf2.fits*')			

	elif 'Version CIAO' in creator_key:
		hist = get_history_records(spec_crate)
		pha_root = ''

		for i in range(0,len(hist)):
			if ':root=' in hist[i][1]: #find the line where the :root command was used
				root_line = hist[i][1].split('=',1)[1].strip() #strip the unnecessary stuff but leaves the extra spaces
				pha_root = root_line.split(' ')[0] #remove everything after the last character assuming they are separated by spaces
			else:
				print('ERROR, cant find the pha_root value')

		if resp_dir == None:
			arf_list = glob.glob(f'tg/{pha_root}*arf2.fits*')
			rmf_list = glob.glob(f'tg/{pha_root}*rmf2.fits*')
		else:
			arf_list = glob.glob(f'{resp_dir}/{pha_root}*arf2.fits*')
			rmf_list = glob.glob(f'{resp_dir}/{pha_root}*rmf2.fits*')

	#do some basic checking to make sure the ARFs and RMFs are the same obsID and same source and reorder them to match the order in the pha2_file
	


	return(matched_arf_list, matched_rmf_list)



#### TESTING END

######### MAIN CrissCross RUN FUNCTION ##############



def run_crisscross(working_dir = 'criss_cross_output', input_dir = 'input_files', main_list = 'input_files/full_coup_src_list.csv', subset_arr_list = 'input_files/subset_onc.csv'):
	"""""
	Main function for running criss cross.

	working_dir = a directory for holding the output of CrissCross. If it does not exist then it will be made.
	input_dir = the directory which holds the relevant files (evt2.fits, wavedetect source tables, crisscross ARF tables) for running criss cross. 
	main_list = a csv file with columns RA, DEC, ID of source positions. This can include sources outside of an individual chandra obsID FOV
	subset_arr_list = a csv file with columns RA, DEC, ID of sources to generate spectral confusion tables for (the sources bright enough for HETG spectral fitting).
	"""""


	#NOTE--> consider more convenient ways for users to input fits files and source lists. Should this be its own function? Should I use stk_build? This will take some more work to figure out best way for CIAO.

	#working_dir='criss_cross_output' #dir you will be working in where all the output will be saved

	#input_dir = 'input_files' #dir with the necessary input files (fits files, wavedetect lists, src_list, etc)

	fits_list = sorted(glob.glob(f'{input_dir}/*repro_evt2.fits')) #users need a list of evt2 fits files to operate on. 

	wavedetect_list = sorted(glob.glob(f'{input_dir}/*wavdetect*')) #users need a list of wavedetect source fits files to later MATCH to main_list and subset_arr_list. 

	#main_list = f'{input_dir}/full_coup_src_list.csv' # CSV list of known sources that are in the field of view in the format ('RA', 'DEC', 'ID') with RA and Dec in degrees. This can include sources also outside of a particular field of view. These will be matched to a wavedetect output file to obtain the number of 0th order counts for each source detected.

	#subset_arr_list = f'{input_dir}/subset_onc.csv' # list of sources to determine if confusion occurs for spectral fitting in the format ('RA', 'DEC', 'ID') with RA and Dec in degrees. Typically, this would be a small subset of the sources in the FOV (main list) and only those bright enough for HETG spectral fitting. 




	#resetting the ardlib
	ardlib.punlearn()


	#create the output files directory
	make_output_dir(working_dir)

	#use dmkeypar to obtain the obsid and roll angle for each observation for file naming purposes
	obsid = np.empty(len(fits_list), dtype=object)
	roll_nom_arr = np.empty(len(fits_list), dtype=float)
	heg_ang_arr = np.empty(len(fits_list), dtype=float)
	meg_ang_arr = np.empty(len(fits_list), dtype=float)

							
	for i in range(0,len(fits_list)):
		obsid[i] = get_header_par(fits_file = fits_list[i], keyword_par = 'obs_id')
		roll_nom_arr[i] = get_header_par(fits_file = fits_list[i], keyword_par = 'ROLL_NOM')

		grating_rotang = read_file(f'{fits_list[i]}[REGION]') #always reads the region block because the block number is variable
		heg_ang_arr[i] = grating_rotang.ROTANG.values[1] #tg_part = 1
		meg_ang_arr[i] = grating_rotang.ROTANG.values[2] #tg_part = 2


	wavedetect_list = wavedetect_match_obsid(fits_list_par = fits_list, wavedetect_list_par = wavedetect_list) #make sure wavedetect source tables are in same order as evt2 fits files.


	#make all the output dirs and then create an array from them to store for file output at end

	output_dir_list = []
	for i in range(len(fits_list)):
		os.system(f'mkdir -p {working_dir}/output_dir_obsid_{obsid[i]}')
		output_dir_list.append(f'{working_dir}/output_dir_obsid_{obsid[i]}')


	#for k in range(0,2):
	for k in range(len(fits_list)):
	#for k in range(1,3):
	#for k in range(3, len(fits_list)): #if you want to start at a specific spot in the fits list


		ardlib.punlearn()

		#start the time logger for printing steps to the screen
		time_log_start, time_log_counter = time_logger(mode='start')

		#print the tweakable paramters to the screen and then record them near the end along with the time it took to run.
		print('\n')
		print('This run is for observation %s' % fits_list[k])
		print('This run is using the wavedetect file %s' %wavedetect_list[k])
		print('The contamination offset threshold is set to %s pixels.' %contam_offset_thresh)
		print('The counts threshold to be considered a spectrum of interest is set to %s counts.' % counts_intercept_thresh_i)
		print('The counts threshold to be considered a potential contaminating spectral source is %s counts.' %counts_intercept_thresh_j)
		print('The counts threshold to be considered a potential 0th order point source contaminating source is %s counts.' %counts_contam_pntsrc_thresh)
		print('The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is %s pixels' % dist_to_super_bright_perp)
		print('The fraction of the OSIP window to include when considering two arm overlaps is set at %s percent ' % (osip_frac*100))
		print('The minimum counts in Src Bs 0th order to assess total arm confusion in source A is %s ' % (min_HETG_counts))

		#set a few obsid_specific parameters
		heg_ang = heg_ang_arr[k]
		meg_ang = meg_ang_arr[k]
		roll_nom = roll_nom_arr[k]
		
		print('The HEG/MEG angles for this observation are %s and %s degrees.' % (heg_ang, meg_ang))

		print('The roll angle of this observation is %s' % roll_nom)


		#save the RA, DEC and SRCID from the main input list
		RA_wcs, DEC_wcs, srcID = load_sourcelist_csv(main_list)

		#save the RA, DEC and SRCID from the subset input list
		subset_RA, subset_DEC, subset_arr = load_sourcelist_csv(subset_arr_list)

		#convert from RA/DEC in degrees to Chandra Sky physical coordinates
		src_pos_x, src_pos_y = calc_physical_coords(fits_par=fits_list[k], RA_par = RA_wcs, DEC_par = DEC_wcs)


		time_message = 'Finished converting RA/DEC into chandra coords'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)


		#match input source list to wavedetect table to catalog 0th order counts for each source in each obsid
		final_match_arr, final_dist_arr, counts = find_closest_source(src_x_arr = src_pos_x, src_y_arr = src_pos_y, wave_file = wavedetect_list[k], max_offset = 3.0)

		#create an output file of the input source list with the wave-detect-matched 0th order counts
		write_matched_file(srcid_arr = srcID, ra_arr = RA_wcs, dec_arr = DEC_wcs, counts_arr = counts, fileroot = f'src_list_{obsid[k]}')

		#calculate off-axis angle for each input source
		src_off_axis = calc_off_axis_angle(fits_list_par = fits_list[k], src_pos_x_par = src_pos_x, src_pos_y_par = src_pos_y)

		#Print to the screen the number of sources that satisfy the above conditions as well as the total number of sources in input list.
		src_num = len(src_pos_x)

		counts_intercept_num = len(counts[counts > counts_intercept_thresh_i]) #will count the number of sources that are above the threshold #https://stackoverflow.com/questions/12995937/count-all-values-in-a-matrix-greater-than-a-value

		counts_contam_pntsrc_num = len(counts[counts > counts_contam_pntsrc_thresh]) #number of point sources that are above some thresh that are capable of contaminating the other sources. Note, couldn't get it to easily work to only report the this value based on thenumber of sources bright enough for spectra in the first place. Instead it just counts all sources above X counts.

		print("The total number of sources input is %s." % (src_num))
		print("The number of sources above the contamination intercept threshold of %s counts for ObsID %s is %s." % (counts_intercept_thresh_i,obsid[k], counts_intercept_num))

		#calculate relevant parameters for when two lines intersect in the Chandra FOV
		m_heg, m_meg, b_heg, b_meg, xintercept_heg, xintercept_meg, yintercept_heg, yintercept_meg, xoff, yoff = determine_line_intersect_values(src_pos_x_par = src_pos_x, src_pos_y_par = src_pos_y, heg_ang_par = heg_ang, meg_ang_par = meg_ang)


		time_message = 'Finished calculating XY intercepts for all sources in the field of view.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

		#########SPECTRAL CONFUSION START ############

		#create the spectral confusion nested dictionary for all sources before filling in values using the next functions.
		spec_conf = conf_dict(num_sources = len(src_pos_x), highest_order = 3)

		#Calculate where two spectral arms intersect eachother for every source 
		spec_conf = spec_confuse_wave(spec_conf, src_pos_x, src_pos_y, 'heg', xintercept_heg, yintercept_heg, counts, counts_intercept_thresh_i, counts_intercept_thresh_j, P_heg, 3, roll_nom_par = roll_nom)
		spec_conf = spec_confuse_wave(spec_conf, src_pos_x, src_pos_y, 'meg', xintercept_meg, yintercept_meg, counts, counts_intercept_thresh_i, counts_intercept_thresh_j, P_meg, 3, roll_nom_par = roll_nom)

		#Calculate the wave_low and wave_high bounds for spectral confusion which is based on the HETG geometry
		spec_conf = spec_confuse_wave_bounds(spec_conf, highest_order= 3, src_pos_x_par = src_pos_x)
		
		#Determine OSIP wavelength range expected at the location and energy of spectral confusion for each source.
		spec_conf = spec_calc_osip_bounds(spec_conf, highest_order = 3, osip_frac_par = osip_frac, subset_arr_par = subset_arr, src_pos_x_par = src_pos_x, fits_list_par=fits_list[k], obsid_par = obsid[k])

		#determine whether spectral confusion has occured and set the appropriate arm/order flags
		spec_conf = spec_flag_set(spec_conf, src_pos_x_par = src_pos_x, src_pos_y_par = src_pos_y, subset_arr_par = subset_arr, fits_list_par = fits_list[k], input_dir_par = input_dir)


		time_message = 'Finished assigning spectral confusion.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)



		#########POINT SOURCE CONFUSION START ############

		#CREATE the point source confusion dictionary to hold all relevant parameters
		pntsrc_conf = conf_dict(num_sources = len(src_pos_x), highest_order = 3)

		#calcluates perp_distance_to_spec and 'intersect distance' for all point sources
		pntsrc_conf, perp_dist_to_spec_heg, r0_offset_dist_from_contam_heg = pntsrc_dist_to_spec(pntsrc_conf_par=pntsrc_conf, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, xoff_par=xoff, yoff_par=yoff, m_arm_par=m_heg, b_arm_par=b_heg, arm_ang_par=heg_ang, arm_par='heg')

		pntsrc_conf, perp_dist_to_spec_meg, r0_offset_dist_from_contam_meg = pntsrc_dist_to_spec(pntsrc_conf_par=pntsrc_conf, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, xoff_par=xoff, yoff_par=yoff, m_arm_par=m_meg, b_arm_par=b_meg, arm_ang_par=meg_ang, arm_par='meg')	

		#Determines the wavelegth where point source confusion may occur 

		#HEG
		pntsrc_conf = pntsrc_confuse_wave(pntsrc_conf_par=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg ,src_pos_x_par=src_pos_x, P_arm_par=P_heg, mm_per_pix=mm_per_pix, X_R=X_R, arm_par='heg', roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, counts_par=counts, contam_offset_thresh_par=contam_offset_thresh, counts_intercept_thresh_i_par=counts_intercept_thresh_i, counts_contam_pntsrc_thresh_par=counts_contam_pntsrc_thresh)

		#MEG
		pntsrc_conf = pntsrc_confuse_wave(pntsrc_conf_par=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, src_pos_x_par=src_pos_x, P_arm_par=P_meg, mm_per_pix=mm_per_pix, X_R=X_R, arm_par='meg', roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, counts_par=counts, contam_offset_thresh_par=contam_offset_thresh, counts_intercept_thresh_i_par=counts_intercept_thresh_i, counts_contam_pntsrc_thresh_par=counts_contam_pntsrc_thresh)


		time_message = 'Finished calculating point source confusion wavelengths.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)

		#determine whether confusion occurs for all point sources
		pntsrc_conf = pntsrc_confuse_wave_bounds(pntsrc_conf_par=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg, fits_list_par = fits_list[k], subset_arr_par=subset_arr, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, arm_par='heg', moritz_factor_par=0.1, logfile_par=f'pnt_src_confuse_{obsid[k]}_log.txt')
		pntsrc_conf = pntsrc_confuse_wave_bounds(pntsrc_conf_par=pntsrc_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, fits_list_par = fits_list[k], subset_arr_par=subset_arr, src_pos_x_par=src_pos_x, src_pos_y_par=src_pos_y, arm_par='meg', moritz_factor_par=0.1, logfile_par=f'pnt_src_confuse_{obsid[k]}_log.txt')

		#sets the flags for point source confusion
		pntsrc_conf_par = pntsrc_flag_set(pntsrc_conf_par=pntsrc_conf, src_pos_x_par=src_pos_x, arm_par='heg', subset_arr_par = subset_arr)
		pntsrc_conf_par = pntsrc_flag_set(pntsrc_conf_par=pntsrc_conf, src_pos_x_par=src_pos_x, arm_par='meg', subset_arr_par = subset_arr)


		time_message = 'Finished assigning point source confusion.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)		



		##########ARM CONFUSION START ############################

		#creates the arm confusion nested dictionary based on the total number of source in the input list
		arm_conf = arm_conf_dict(num_sources = len(src_pos_x), highest_order = 3)

		#Calculates the ratio of 0th order counts (net_counts_confuser / net_counts_confused) and determines the distance from the confused 0th order to the confuser 0th order.
		arm_conf = arm_confuse_wave(arm_conf_par=arm_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_heg, src_pos_x_par=src_pos_x, P_arm_par=P_heg, arm_par='heg', arm_ang_par=heg_ang, roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, r0_offset_dist_from_contam_arm_par=r0_offset_dist_from_contam_heg, counts_par = counts, subset_arr_par = subset_arr)
		
		arm_conf = arm_confuse_wave(arm_conf_par=arm_conf, perp_dist_to_spec_arm_par=perp_dist_to_spec_meg, src_pos_x_par=src_pos_x, P_arm_par=P_meg, arm_par='meg', arm_ang_par=meg_ang, roll_nom_par=roll_nom, src_off_axis_par=src_off_axis, r0_offset_dist_from_contam_arm_par=r0_offset_dist_from_contam_meg, counts_par = counts, subset_arr_par = subset_arr)

		#determine which of the positive or negative order the confuser 0th order source falls on
		arm_conf = determine_confused_order(arm_conf_par=arm_conf, src_pos_x_par = src_pos_x, arm_par = 'heg')
		arm_conf = determine_confused_order(arm_conf_par=arm_conf, src_pos_x_par = src_pos_x, arm_par = 'meg')

		#calcluates the resolution as a function of energy for heg/meg
		#NOTE--> these values only need to be calculated once PER RUN. Doesn't depend on obsid or location or anything.
		res_power_heg_maxed, hetg_arr_heg = calc_ccd_energy_res(arm_par='heg')
		res_power_meg_maxed, hetg_arr_meg = calc_ccd_energy_res(arm_par='meg')

		#Based on the distance between 0th orders for arm confusion, determine the wavelength range where arm confusion occurs FOR EACH ORDER and set flags appropriately
		arm_conf = arm_flag_set(arm_conf_par=arm_conf, arm_par='heg', src_pos_x_par = src_pos_x, res_power_arm_maxed_par=res_power_heg_maxed, hetg_arr_arm_par=hetg_arr_heg, subset_arr_par = subset_arr, nsig_par=6)
		arm_conf = arm_flag_set(arm_conf_par=arm_conf, arm_par='meg', src_pos_x_par = src_pos_x, res_power_arm_maxed_par=res_power_meg_maxed, hetg_arr_arm_par=hetg_arr_meg, subset_arr_par = subset_arr, nsig_par=6)



		time_message = 'Finished assigning arm confusion.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)


		#using the results of the individual confusion functions above, set the main confusion flag for every source. E.g., if any order is confused then main confusion flag is set to 'confused'.
		spec_conf = main_flag_set(conf_dict_par = spec_conf, src_pos_x_par = src_pos_x, subset_arr_par = subset_arr)
		pntsrc_conf = main_flag_set(conf_dict_par = pntsrc_conf, src_pos_x_par = src_pos_x, subset_arr_par = subset_arr)
		arm_conf = main_flag_set(conf_dict_par = arm_conf, src_pos_x_par = src_pos_x, subset_arr_par = subset_arr)

		#Call write_full_conf_table to produce the 'full' and 'consolidated' tables for each source in the run obsID.
		for i in subset_arr:
			write_full_conf_table(spec_conf_par = spec_conf, pntsrc_conf_par = pntsrc_conf, arm_conf_par = arm_conf, row_num = i, srcID_par = srcID, counts_par = counts, working_dir_par = working_dir, remove_clean = 'yes', obsid_par = obsid[k], consolidate_table = True)

		#move output files into final directories and cleanup
		end_of_run_cleanup(output_dir_list_par = output_dir_list[k], obsid_par = obsid[k], working_dir_par = working_dir)




		time_message = 'Finished Running CrissCross!.'
		time_log_counter = time_logger(mode='update', time_started = time_log_start, time_counter = time_log_counter, message=time_message)


		log_file = open('LOG_'+obsid[k]+'.txt', 'w')	
		
		log_file.write('This run is for observation %s. \n' % fits_list[k])
		log_file.write('The wavdetect source list used for this observation is %s. \n' % wavedetect_list[k])
		log_file.write('The roll angle of this observation is %s degrees. \n' % round(roll_nom,2))
		log_file.write('MEG angle = %s degrees and HEG angle = %s degrees. \n' % (round(meg_ang,2),round(heg_ang,2)))
		if roll_nom > 80 and roll_nom < 100:
			log_file.write('WARNING, ROLL NOM IS %s so plus and minus grating orders may be confused and then everything could be wrong. \n' % roll_nom)
		if roll_nom > 260 and roll_nom < 280:
			log_file.write('WARNING, ROLL NOM IS %s so plus and minus grating orders may be confused and then everything could be wrong. \n' % roll_nom)
		log_file.write('\nThe contamination offset threshold is set to %s pixels. \n' %contam_offset_thresh)
		log_file.write('The counts threshold to be considered a spectrum of interest is set to %s counts. \n' % counts_intercept_thresh_i)
		log_file.write('The counts threshold to be considered a potential contaminating spectral source is %s counts. \n' %counts_intercept_thresh_j)
		log_file.write('The counts threshold to be considered a potential 0th order point source contaminating source is %s counts. \n' %counts_contam_pntsrc_thresh)
		log_file.write('The distance in pixels required for two very bright sources to be considered for ARM REMOVAL --tis but a scratch-- is %s pixels. \n' % dist_to_super_bright_perp)
		log_file.write('The fraction of the OSIP window to include when considering two arm overlaps is set at %s percent. \n' % (osip_frac*100))
		log_file.write('\nThe total number of sources input is %s. \n' % (src_num))
		log_file.write('The number of sources above the contamination intercept threshold of %s counts for ObsID %s is %s. \n' % (counts_intercept_thresh_i,obsid[k], counts_intercept_num))
		log_file.write('The minimum counts in Src Bs 0th order to assess total arm confusion in source A is %s. \n ' % (min_HETG_counts))

		log_file.write('The HEG/MEG angles for this observation are %s and %s degrees. \n ' % (heg_ang, meg_ang))	

		if roll_nom > 80 and roll_nom < 100:
			log_file.write('WARNING, ROLL NOM IS %s. Confusion results from roll angles very close to 90 degrees may be incorrect' % roll_nom)
		
		if roll_nom > 260 and roll_nom < 280:
			log_file.write('WARNING, ROLL NOM IS %s. Confusion results from roll angles very close to 270 degrees may be incorrect' % roll_nom)

		total_time = time_logger(mode='end',time_started=time_log_start)

		log_file.write('\nThe total elapsed time for obsID %s is %s minutes. \n' % (obsid[k], total_time))

		log_file.close()
		
		#now we move the log to the output directory
		subprocess.call("mv LOG_%s.txt %s" %(obsid[k], output_dir_list[k]), shell=True)





		