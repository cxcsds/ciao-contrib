### CrissCross Summary

Criss Cross is designed to allow users to plot, model and fit Chandra High Energy Transmission Grating (HETG) spectra that are extracted from a Chandra field of view with a large number of other astrophysical X-ray sources. The HETG instrument will disperse events from **all** sources in a field of view and if there are several bright X-ray sources then there is a potential for confusion to occur. Confusion is a term used here for special scenarios where standard HETG spectral extraction of a source may erroneously assign events from a different source in the field of view to the extracted source. This would result in events from a different source confusing the spectrum of your extracted source. 

CrissCross identifies when spectral confusion occurs for a list of input sources and generates confusion tables which identify the wavelength/energy in each source's spectrum that are likely to include X-ray events from other astrophysical sources. The user can then choose to ignore, remove, model or angrily shake their fist at these events during their spectral fitting analysis. **Users are encouraged to try CrissCross using the included jupyter notebook tutorial 'criss_cross_tutorial.ipynb'. It provides an end-to-end example of running CrissCross on an HETG observation of a crowded stellar cluster and extracting a cleaned spectrum.**


### How does CrissCross work?


The criss_cross routine takes advantage of the characteristic 'X' shape the Chandra-HETG instrument makes when dispersing X-ray light onto the ACIS-S CCDs. X-ray sources observed with the Chandra-HETG instrument cast an X shape onto the detector. For each source, the center of this 'X' is located at the position of the (zeroth-order) X-ray source in the field of view. While technically all X-ray sources cast their own X shape, the majority in most Chandra fields-of-view are too faint to disperse enough events onto the detector for high resolution X-ray spectroscopy purposes. As a result only the brightest X-ray sources will produce this X shape visible by eye in an HETG event file.  If there are two or more bright sources in the same field of view then their respective X shapes likely intersect with each other somewhere on the detector. In other words, if you were to extract HETG spectra from each of these sources using standard CIAO tools, there is are locations in each spectrum that could contain events from other sources. Throughout this documentation, this scenario is referred to as 'confusion'. Confusion occurs when events from another source end up in the spectrum of your source of interest during extraction.

Chandra/CIAO already has a mechanism to handle some level of confusion. Energy/wavelength as a function of distance from the center of the HETG 'X' shape is known based on the gratings dispersion equation and the instrumental setup. When the energy of an X-ray event, as measured by the ACIS CCDs, is very different than what is expected at the location in the spectral arm (distance from center of X) then CIAO will remove these events automatically using Order Sorting Integrated Probability tables in the CALDB. However, there can be cases where the energy of confusing events from another source is the SAME as what is expected from the spectrum of the extracted source. These cases are currently not handled in CIAO and are exactly what is identified by criss_cross. For the sake of argument, lets assume you are interested in the HETG spectrum of 'Src A' and there is another source in the field of view called 'Src B'. The criss_cross routine handles all three possible types of confusion:

1) **[Spectral Confusion]**   occurs when the dispersed spectrum of Src B intersects with the X shape of Src A AND Src B is bright enough to disperse a meaningful number of events. What is 'a meaningful number' of events? When spectral confusion CAN occur based on the geometry of two sources the wavelength of confusion is calculated from the gratings equation. Both the confused (Src A) and confuser (Src B) zeroth order point sources are analyzed to determine how many Nth order (1st, 2nd, 3rd) dispersed counts exist in the energy bandpass where confusion can occur. If this ratio (src B / src A) is > spec_confuse_limit (default = 10%) then CrissCross marks this as confusion. This calculation accounts for the effective area at the location of confusion as well as the efficiencies of different spectral orders (e.g., if MEG+3 from src B is confusing HEG+1 of source A).

2) **[Point Source Confusion]** occurs when the zeroth order point source of SRC B lands on/near (is coincident with) the dispersed spectral arm of Src A. The Src B 0th order will include events of all energies in the Src B spectrum and is likely to cause confusion in the extracted HETG spectrum of Src A. The proximity of Src B (contam_offset_thresh) is used to determine if confusion can occur. Similar to spectral confusion, the Src B zeroth order spectrum is analyzed to determine the number of counts in the wavelength range of Src A where confusion could occur. If the ratio of (Src B / Src A) > 10% then it is marked as confused. The PSF size of the potential confuser (Src B) is taken into account and only the events that overlap with the spectrum are considered as potential confusing events. Typically, most sources in the field of view are too faint to meaningfully dispersed HEG/MEG counts so a point source confuser will only confuse a small wavelength range of the Src A spectrum. However, if Src B is sufficiently bright then it will cause ARM confusion (see next).

3) **[Spectral ARM Confusion]**  occurs when Src B is bright AND lands on/near the arm of Src A. In this case, Src B is bright enough to disperse its events into an X-shape and if it lands on the arm of Src A that means it will disperse events directly along the entire spectral arm of Src A. This situation is unfortunate as it potentially confuses a large portion of the Src A spectrum. When ARM confusion potentially occurs, the distance between the Src A and Src B 0th orders (in the dispersion direction) dictates how much of the arm is likely to be confused. The closer the sources are, the more of the spectral arm is confused. CrissCross will use the distance between these sources to identify how much of the arm suffers confusion. 


#### Description of CrissCross INPUT and OUTPUT

**REQUIRED NPUT**


1) **main_list**:  An ascii or TSV file with columns 'RA, DEC, ID' for each known X-ray source in the field of view. CrissCross must know what sources exist in the field of view in order to calculate where potential confusion can occur. This file can include sources that may not fall on the CCD in every observation since roll angles can change. The ID column must be an integer and the RA and DEC must be in degrees.

2) **subset_src_list**:  A ascii or TSV file with columns 'RA, DEC' for each source that you wish to calculate confusion for. These will be a subset of sources in the 'main_list' that are bright enough for HETG spectral extraction. These sources must match sources in the main_list. The parameters 'clean_single_RA' and 'clean_single_DEC' can be used instead of subset_src_list to calculate confusion for only a single source. The RA and DEC must match a source in the main_list file.

4)  **input_dir**: A directory that holds two fits tables necessary for spectral confusion calculations (MEG_Nth_0th_order_ratios_mkarf.fits, HEG_Nth_0th_order_ratios_mkarf.fits).
 
5)  **evt2_file**:  An individual evt2 file or a list of evt2 files for each observation the user wishes to run. 


**OUTPUT**

output is saved to working_dir/output_dir_obsid_{obsid_num}

1)  **confusion_output_files/table_fits_data**:  This directory holds all of the confusion fits tables for sources in the 'subset_src_list':

    a)  **confused_src_{srcID}_full_obsID_{obsid_num}.fits**  table that includes ALL confusion information about the confused source for every order for every arm and for every confusion type. 

    b)  **confused_src_{srcID}_consolidated_obsid_{obsi_num}.fits**  table that includes ONLY the information from flag = 'confused' or flag = 'warn' sources of confusion. Every row of this table includes a potential instance of 	confusion and can be programmatically used to ignore or plot sources of confusion in spectra.

2)  **src_list_{obsid_num}.txt**:   A CSV or TXT file in the format 'RA', 'DEC', 'ID', 'Zeroth_order_counts' showing the matched input source list to the wavedetect file for the appropriate observation.

3)  **LOG_{obsid_num}.txt**:  A log file which includes the CrissCross parameter values.

4)  **pnt_src_confuse_{obsid_num}_log.txt**:  a log file for the point source confusion. Most of this is not necessary for end user.

5)  **spec_confuse_{obsid_num}_log.txt**:  a log file for the spectral source confusion. Most of this is not necessary for end user.



This code was created by D. Principe (principe@space.mit.edu) with contributions from M. Guenther and D. Huenemoerder.
