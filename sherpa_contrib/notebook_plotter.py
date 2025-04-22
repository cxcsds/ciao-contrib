from ipywidgets import widgets, HBox, VBox, Layout
from sherpa.astro.ui import *
import numpy as np
import matplotlib.pyplot as plt    

def notebook_plotter(model_var, dataset_id = 1, model_resolution = 0.001,  autoscale = 'xy', xlim_low = 0.3, xlim_high = 10, ylim_low = 0.001, ylim_high = 10, log_axis = 'none', plot_type = 'model_unconvolved',  figsize_x = 10, figsize_x_min = 0.1, figsize_x_max = 30, figsize_y=5, figsize_y_min=0.1, figsize_y_max = 30, limit_style = 'soft', widget_step = 0.001):

    '''
    
    \nThis functions creates the interactive jupyter notebook plotting window allowing users to visualize changes in model parameters and how that may affect spectral fitting. Users can adjust the 'Model Parameters' section of the interactive plot to visualize real-time changes in the underlying spectral model. Users can modify the Plotting Options in the interactive plot to customize what is plotted. This tool is currently a prototype and is meant to demonstrate the usefulness of python ipywidgets in visualizing sherpa data. For full functionality, users should have a dataset loaded with proper responses and a model set (e.g., with load_pha() and set_source() ). Please note, running this tool and modifying the model parameters will change the model values in your sherpa session.
    
        Parameters
        ----------
            model_var: sherpa.models.Model object
            A variable assigned to a sherpa  model. This cannot be a string.
            Example: my_model = (xstbabs.a1 * xsapec.p1)

            dataset_id: int
                The sherpa dataset identifier. The default value is dataset id 1.

            figsize_x_min: float
                The minimum allowable X-axis size of the interactive plotting window.

            figsize_x_max: float
                The maximum allowable X-axis size of the interactive plotting window.

            figsize_y_min: float
                The minimum allowable Y-axis size of the interactive plotting window.

            figsize_y_max: float
                The maximum allowable Y-axis size of the interactive plotting window.           

            limit_style: string
                This parameter can be either 'soft' (default) or 'hard'. Soft limits will set the user-defined limits when plotting the maximum and minumum model parameter values. Hard limits will set the model-defined maximum and minimum model parameter values.

            widget_step: float
                The minimun step to increment the value for all 'Model Parameter' widget sliders.                

            Description of Interactive Plotting Options
            -------------------------------
           model_resolution: float
                Desired spectral resolution of the plotted model in units of keV. The spectral model will be evalulated over an energy/wavelength grid every resolution element. If plotting in wavelength space, model_resolution is automatically converted from keV to Ang.

            autoscale: string
                Whether or not to autoscale the respective axes using the values plotted. 'None' means no autoscaling, 'x' means x-axis only autoscaling, 'y' means y-axis only autoscaling, and 'xy' means both x and y axes are autoscaled.                

            xlim_low: float
                The minimum value for the x-axis plot widget.

            xlim_high: float
                The maximum value of the x-axis plot widget.

            ylim_low: float
                The minumum value for the y-axis plot widget.

            ylim_high: float
                The maximum value for the y-axis plot widget.

            log_axis: string
                Whether or not to plot axes in log-space. 'None' means no log space plotting, 'xlog' means xlog only plotting, 'ylog' means ylog only plotting, and 'loglog' means both x and y are set to log plotting.

            plot_type: string
                This parameter determines what is plotted. 'model_unconvolved' plots the source model using the model resolution and without folding in the instrument response. 'model_convolved' plots the source model convolved with the instruments (ARF+RMF) responses. 'both_models' plots both unconvolved (purple) and convolved models (orange) on the same plot. For this plot_type, plotting options control the unconvolved model plot while the y-axis of the convolved model autoscales to remain within the x and y limits set for the unconvolved model. 'data_and_convolved_model' plots the loaded dataset with the source model convolved with the response. When plotting a convolved model or data, the model_var must be set to the same dataset value as indicated with dataset_id.

            figsize_x: float
                Sets the initial widget x-axis figure size.

            figsize_y: float
                Sets the initial widget y-axis figure size.

         Notes
         -------
         Interactive plotting options can be set by selecting them in the plotting window or directly in the call to the the notebook_plotter() function. 

         Units of model_resolution parameter should always be in keV regardless whether or not set_analysis is set to 'energy' or 'wavelength'. If plotting in wavelength, keV resolution elements are converted to Angstrom.  This tool does not work with other set_analysis() options.              

         Some of the parameter widget boxes and sliders have clickable up and down arrows to adjust parameter values. Only the minimum 'Model Parameter' slider increments can be adjusted using the widget_step parameter. Users can override most parameter values by clicking the values and entering new values using a keyboard.
         
         Examples
         -------

         Define a model and plot the unconvolved model with default notebook_plotter parameters. Here we set a maximum to nH to better facilitate viewing using widgets:

         >>> my_model = (xstbabs.a1 * xsapec.p1)
         >>> a1.nH.max = 50
         >>> notebook_plotter(my_model)

         Plot the same model as previous example with a new resolution of 0.1 keV. Modify the plotting parameters by setting the y-axis in log-scale, setting limits on the x-axis and y figure size while plotting the unconvolved model:  

         >>> notebook_plotter(my_model, model_resolution = 0.1, log_axis = 'ylog', xlim_low = 0.3, xlim_high =10, figsize_y = 3, plot_type = 'model_unconvolved')

         Load a dataset and associated responses with id=2, set a model to the data and then plot the data with the convolved model overlaid:

         >>> load_pha(2,'src2.pi')
         >>> load_arf(2, 'src2.arf')
         >>> load_rmf(2, 'src2.rmf')
         >>> my_model_2 = (xsapec.p1 + xsapec.p2)
         >>> set_source(2, my_model_2)
         >>> notebook_plotter(my_model_2, dataset_id = 2, plot_type = 'data_and_convolved_model')

         Compare the unconvolved and convolved models in the previous example in wavelength (Angstrom) and adjust the minimum widget slider increment for model parameters to be at least 0.1:

         >>> set_analysis('wavelength')
         >>> notebook_plotter(my_model_2, dataset_id = 2, plot_type = 'both_models', widget_step  = 0.1)

    '''    


    ###############################
    #function 1 -- widget_maker

    def widget_maker(model_var, dataset_id, model_resolution, autoscale, xlim_low, xlim_high, ylim_low, ylim_high, log_axis, plot_type, figsize_x, figsize_x_min, figsize_x_max, figsize_y, figsize_y_min, figsize_y_max, limit_style, widget_step):
        '''
        This function collects information about the user-supplied model and creates the appropriate dictionary object where the dictionary keys are the model/UI parameter names and the values are the associated widgets that control them. This function is used by notebook_plotter() when creating the interactive plot.
                            
        Parameters
        ----------
            model_var: sherpa.models.Model object
            A variable assigned to a sherpa  model. This cannot be a string.
            Example: my_model = (xstbabs.a1 * xsapec.p1)
            
            dataset_id: int
                The sherpa dataset identifier. The default value is dataset id 1.            

            figsize_x_min: float
                The minimum allowable X-axis size of the interactive plotting window.

            figsize_x_max: float
                The maximum allowable X-axis size of the interactive plotting window

            figsize_y_min: float
                The minimum allowable Y-axis size of the interactive plotting window.

            figsize_y_max: float
                The maximum allowable Y-axis size of the interactive plotting window            

            limit_style: string
                This parameter can be either 'soft' (default) or 'hard'. Soft limits will set the user-defined limits when plotting the maximum and minumum model parameter values. Hard limits will set the model-defined maximum and minimum model parameter values.

            widget_step: float
                The minimun step to increment the value for all 'Model Parameter' widget sliders.                

            Description of Interactive Plotting Options
            -------------------------------
            model_resolution: float
                Desired spectral resolution of the plotted model in units of keV. The spectral model will be evalulated over an energy/wavelength grid every resolution element. If plotting in wavelength space, model_resolution is automatically converted from keV to Ang.

            autoscale: string
                Whether or not to autoscale the respective axes using the values plotted. 'None' means no autoscaling, 'x' means x-axis only autoscaling, 'y' means y-axis only autoscaling, and 'xy' means both x and y axes are autoscaled.                

            xlim_low: float
                The minimum value for the x-axis plot widget.

            xlim_high: float
                The maximum value of the x-axis plot widget.

            ylim_low: float
                The minumum value for the y-axis plot widget.

            ylim_high: float
                The maximum value for the y-axis plot widget.

            log_axis: string
                Whether or not to plot axes in log-space. 'None' means no log space plotting, 'xlog' means xlog only plotting, 'ylog' means ylog only plotting, and 'loglog' means both x and y are set to log plotting.

            plot_type: string
                This parameter determines what is plotted. 'model_unconvolved' plots the source model using the model resolution and without folding in the instrument response. 'model_convolved' plots the source model convolved with the instruments (ARF+RMF) responses. 'both_models' plots both unconvolved (purple) and convolved models (orange) on the same plot. For this plot_type, plotting options control the unconvolved model plot while the y-axis of the convolved model autoscales to remain within the x and y limits set for the unconvolved model. 'data_and_convolved_model' plots the loaded dataset with the source model convolved with the response. When plotting a convolved model or data, the model_var must be set to the same dataset value as indicated with dataset_id.

            figsize_x: float
                Sets the initial widget x-axis figure size.

            figsize_y: float
                Sets the initial widget y-axis figure size.


            Returns
            -------
                return: dictionary
                This function returns a dictionary of widgets with model parameter fullnames, values, minimum and maximums where min and max are determined by 'soft' or 'hard' limit style. This format is necessary for the notebook_plotter() funciton.


        '''
        #Create lists to hold the model information (model parameter names, values, and soft/hard min/max)
        components_full = [None] * len(model_var.pars)
        components_val = [None] * len(model_var.pars)
        components_soft_min = [None] * len(model_var.pars)
        components_soft_max = [None] * len(model_var.pars)
        components_hard_min = [None] * len(model_var.pars)
        components_hard_max = [None] * len(model_var.pars)

        for i in range(0,len(components_full)):
            components_full[i] = model_var.pars[i].fullname
            components_val[i] = model_var.pars[i].val
            components_soft_min[i] = model_var.pars[i].min
            components_soft_max[i] = model_var.pars[i].max
            components_hard_min[i] = model_var.pars[i].hard_min
            components_hard_max[i] = model_var.pars[i].hard_max
        
        #models come with hard and soft limits. This allows the user to choose the allowable range of values (via the widget) although hard limits would probably rarely be used. 
        if limit_style == 'hard':
            widget_input = (components_full, components_val, components_hard_min, components_hard_max)
        
        if limit_style == 'soft':
            widget_input = (components_full, components_val, components_soft_min, components_soft_max)

        #Create an empty dictionary which we will fill with widget_dictionary.update()
        widget_dictionary = {}

        #a list for all the plotting UI options. These are independent of the models and allow the user control of the plotting interface.
        plotting_list = ['plottingoptions', 'modelparameters', 'model_resolution', 'autoscale', 'xlim_low', 'xlim_high', 'ylim_low', 'ylim_high', 'log', 'plot_type', 'figsize_x', 'figsize_y' ]

        #The first and second dictionary entries MUST be 'plottingoptions' and 'modelparameters'! These will be the UI Box HEADERS and the order of these dictionary keys actually matters to ipywidgets -- it will display them in the ui in order. 
        for i in plotting_list:
                if i == 'plottingoptions':
                    widget_dictionary.update({i: [None]})
                elif i == 'modelparameters':
                    widget_dictionary.update({i: [None]})
                     

        #sanitize widget_step value in case user enters a negative value
        if widget_step < 0:
            widget_step = 0.001

        #Since the norm param is relevant to many models and can have a large range of values, the widget slider option is removed and replaced with a FloatText widget box where the user must type in the value. If not norm, the widget gets a FloatSlider widget.
        norm_checker = 'norm'
        for i in range(len(widget_input[0])):

            if norm_checker in widget_input[0][i]:
                    widget_dictionary.update({widget_input[0][i]: widgets.FloatText(value = widget_input[1][i], step=1E-6, description=widget_input[0][i], layout=Layout(width='91%'), style = {'description_width': 'initial'})}) #floating text much less of a hassle than the rest
            else:
                widget_dictionary.update({widget_input[0][i]: widgets.FloatSlider(value = widget_input[1][i], min= widget_input[2][i], max=widget_input[3][i], step=widget_step, description=widget_input[0][i], readout_format='0.2f', style={'description_width': 'initial', 'handle_color': 'lightblue'})}) 

        #The remaining plotting option keys are added here (after the model information has been added). Note, the 'plotting options' and 'model parameters' are already added at this point as required by the ui_maker() function below. 
        for i in plotting_list:
            if i != 'plottingoptions': 
                widget_dictionary.update({i: [None]})

        
        ### Define the plotting tool widget values:

        #These define the title for each of the two UI columns       
        widget_dictionary['plottingoptions'] = widgets.HTML('<center><p><strong>Plotting Options</strong></p></center>')
        widget_dictionary['modelparameters'] = widgets.HTML('<center><p><strong>Model Parameters</strong></p></center>')
        
        #Adding model energy resolution as user input
        widget_dictionary['model_resolution'] = widgets.FloatText(value = model_resolution, description = 'resolution')

        #axes autoscaling options
        autoscale_options = ['xy', 'x', 'y', 'none']
        widget_dictionary['autoscale'] = widgets.Dropdown(options=autoscale_options, description='autoscale')

        #check to make sure user-input is one of the available options otherwise print warning.
        if autoscale not in autoscale_options:
                print('WARNING -- %s value not correct syntax so %s plotting option will be set to default.' %('autoscale', 'autoscale'))

        #set the value of the autoscale widget to the users choice in function call
        for i in autoscale_options:
                if autoscale == i:
                    widget_dictionary['autoscale'].value = i        
        
        ##Widgets to control the X and Y axis values.
        widget_dictionary['xlim_low'] = widgets.FloatText(value = xlim_low, description='xlim_low')
        widget_dictionary['xlim_high'] = widgets.FloatText(value = xlim_high, description='xlim_high')
        widget_dictionary['ylim_low'] = widgets.FloatText(value = ylim_low, description='ylim_low')
        widget_dictionary['ylim_high'] = widgets.FloatText(value = ylim_high, description='ylim_high')

        #axes log plotting options
        log_options = ['none', 'xlog', 'ylog', 'loglog']
        widget_dictionary['log'] = widgets.Dropdown(options=log_options, description='log_axis')
        
        #check to make sure user input is one of the options and if not then warn them
        if log_axis not in log_options:
                print('WARNING -- %s value not correct syntax so %s plotting option will be set to default.' %('log_axis', 'log_axis'))

        #set the value of the widget to the users choice in function call
        for i in log_options:
                if log_axis == i:
                    widget_dictionary['log'].value = i


        #The allowable plotting options (unconvolved model, model convolved with response, both unconvolved and convolved models, and a plot with the loaded data and a convolved model).
        plottype_options = ['model_unconvolved', 'model_convolved', 'both_models', 'data_and_convolved_model']
        widget_dictionary['plot_type'] = widgets.Dropdown(options=plottype_options, description='plot_type')

        #check to make sure user input is one of the options and if not then warn them
        if plot_type not in plottype_options:
                print('WARNING -- %s value not correct syntax so %s plotting option will be set to default.' %('plot_type', 'plot_type'))

        #set the value of the widget to the users choice in function call
        for i in plottype_options:
                if plot_type == i:
                    widget_dictionary['plot_type'].value = i

        

        #Adjusts the plotting window size in the notebook
        widget_dictionary['figsize_x'] = widgets.FloatSlider(value=figsize_x, min = figsize_x_min, max = figsize_x_max, step = 0.1, description='figsize_x', style={'handle_color': 'darkblue'})
        widget_dictionary['figsize_y'] = widgets.FloatSlider(value=figsize_y, min = figsize_y_min, max = figsize_y_max, step = 0.1, description='figsize_y', style={'handle_color': 'darkblue'})

        #This adds the 'plotting_list' to the dictionary which is a list of variables for the plotting options. This dictionary entry is important for ui_maker() because it is a neutral way to identify how many model parameters the users model has (total params minus the set plotting_params). This is helpful when needing to loop through model parameters. 
        widget_dictionary.update({'ui_keywords': plotting_list})


        return(widget_dictionary)        
        



    ###############################
    #Function 2 -- UI maker

    def ui_maker(input_widget_dictionary):

        '''
        This function takes the widget dictionary created by widget_maker and generates the user interface object necessary for plotting. The plotting object consists of a left column with the model parameters and a right column with the plotting options. This function separates the appropriate dictionary keys/values into the left and right columns creating a ui_object to be called in notebook_plotter().
                            
            Parameters
            ----------
                input_widget_dictionary:dictionary
                A dictionary produced by widget_maker that contains model and UI parameter and widget keys/values.                

            Returns
            -------
                return: ui_export
                An object necessary for the notebook_plotter() function.

        '''


        #Create a copy of the input dictionary and act on that so when keys are deleted it won't affect variables outside this function.
        widget_dictionary = input_widget_dictionary.copy()

        #grabbing the list of the ui keys generated by widet_maker() so they can be separated from the (variable) model parameters to be used in the right ui box.
        widget_ui_keys = widget_dictionary['ui_keywords']

        #Remove the ui keywords from the dictionary after saving them to a list so it doesn't get carried forward. We only need this list to control the loops.
        widget_dictionary.pop('ui_keywords')
        
        #MODEL PARAMETER UI BOX -- copy the widget_dictionary and remove the ui_keywords/values (except the 'modelparameter' keyword which needs to remain).
        widget_breakup_1 = widget_dictionary.copy()

        for i in widget_ui_keys:
                if i in widget_breakup_1 and i != 'modelparameters':
                    widget_breakup_1.pop(i)      
        
        #PLOTTING OPTIONS UI BOX -- create an empty dictionary to later fill with only the ui_keywords (except model parameters)
        widget_breakup_2 = {}
                            
        for i in widget_ui_keys:
                if i in widget_dictionary and i != 'modelparameters':
                    widget_breakup_2.update({i: widget_dictionary[i]}) 


        #The HBox syntax needs just the dictionary values (the widgets) and not the keys
        widget_model_components  = (list(widget_breakup_1.values()))
        widget_plotting_components = (list(widget_breakup_2.values()))
        
        #you can add layout to either the widgets for the ui_export. Here we add some padding around each widget box so it looks nicer
        widget_layout = Layout(display='inline-block',
                               padding = '0px 10px 0px 30px', # top | right | bottom | left 
                               flex_flow='column')

        left_widgets = VBox(widget_plotting_components, layout = widget_layout)
        right_widgets = VBox(widget_model_components, layout = widget_layout)
        
        ui_export = HBox(children=[left_widgets,right_widgets])

        return(ui_export)


    ###############################
    #Function 3 -- updates the models for plotting

    def model_widget_plotter(**args):
        
        '''
        This function controls what is being plotted and updated using sherpa commands and the user input in the GUI. This function is what is called by widgets.interactive_output() along with the UI to create the interactive plot. Several important features are carried out in this function including: assigning the widget values to those set by the user in the interactive plotter, determining whether the sherpa analysis is being performed in wavelength or energy space to plot the same units in the interactive plotter, evaluating source models over a grid with a specified model resolution, and to warn users if the approrpraite data or responses are not loaded when they try to plot something that needs them.
                            
            Parameters
            ----------
                this function is called with widgets.notebook_plotter with a dictionary produced by widget_dict(). The arguments are the widget_dict keys and values.

        ''' 
    

        #########SETTING THE MODEL PARAMETERS IN THE WIDGETS#############

        #make a copy of the input arguments and remove (pop) the ui_keyword arguments so it loops through only the model arguments with set_par. 
        model_param_dictionary = args.copy()

        #remove the ui_keyword items so only the model parameters remain. Note, the widget_ui_keys list is created in widget_maker() function. 
        for i in widget_ui_keys:
                if i in model_param_dictionary:
                    model_param_dictionary.pop(i)

        for i in model_param_dictionary:
            set_par(i, model_param_dictionary[i])

        #########EVALUATING THE UNCONVOLVED MODEL OVER THE ENERGY AND WAVELENGTH GRID#############

        #this sets up the energy grid over which all the models will get evaluated. The energy grid range can be a variable later for users to choose but for now its 0.2 15.01 keV.

        #determine if sherpa session is using wavelength or energy which will control what the interactive plot shows. If no analysis type is set then users can still create model variable and plot model.
        try:
            analysis_type = get_analysis()
        except:
            analysis_type = 'analysis_not_set'
            #print('WARNING -- anaylsis type not set so model is assumed to be plotting in energy (keV) with units of photons s$^{-1}$ cm$^{-2}$ keV$^{-1}$')

        #regardless of 'get_analysis()' value, models are evaluated in energy space and then converted to wavelength if sherpa session is in wavelength.
        egrid_energy = np.arange(0.2, 15.01, args['model_resolution']) #note, sherpa 'plot_source' resolution is 0.01
        elow_energy = egrid_energy[:-1] #removes last element of egrid_energy
        ehi_energy = egrid_energy[1:] #removes the first element of egrid_energy
        emid_energy = (elow_energy + ehi_energy) / 2          
                    
        model_y_energy = model_var(elow_energy,ehi_energy)/args['model_resolution'] #note, have to divide by resolution to get units correct
        
        #Make the plots in energy or wavelength depending on the set_analysis value chosen in sherpa.
        if analysis_type == 'energy':

            xunit = 'Energy [keV]'
            yunit_unconvolved = 'photons s$^{-1}$ cm$^{-2}$ keV$^{-1}$'

            emid = emid_energy
            model_y = model_y_energy
            
        elif analysis_type == 'wavelength':

            xunit = 'Wavelength [Angstrom]'
            yunit_unconvolved = 'photons s$^{-1}$ cm$^{-2}$ A$^{-1}$'
            
            planck = 4.135667696E-15 # eV * Hz^-1
            c= 2.99792458E8 # m/s

            #convert the energy grid (x axis) to wavelength in Angstrom
            emid_wave = 1E10* ((planck*c) / (1000*emid_energy)) #convert the energy (keV) grid to Angstrom
            emid = emid_wave

            #NOTE-- apparently evaluating sherpa models will always be done in keV even if set_anaylsis is 'wavelength'. So here the model is converted in energy space from units of photons/s/cm2/keV to photons/s/cm2/Angstrom
            model_y = (model_var(elow_energy,ehi_energy)/(args['model_resolution']/emid_energy)) * ( (1000 * emid) / (1E10*planck*c)) #note, have to divide by (resolution/energy) to get units correct

        #This option allows users to create a model without loading any dataset or responses and see how the model looks at different resolutions. HOWEVER it assumes model is in energy space.
        elif analysis_type == 'analysis_not_set':

            xunit = 'Energy [keV]'
            yunit_unconvolved = 'photons s$^{-1}$ cm$^{-2}$ keV$^{-1}$'
            emid = emid_energy
            model_y = model_y_energy

        #for now, get_analysis() must return either energy or wavelength or be set to 'analysis_not_set' for users who want to look only at models. This tool does not currently support set_analysis =  'bins' or 'channels'.
        else:

            print()
            print('ERROR -- set_analysis must be either "wavelength" or "energy" to display unconvolved models or data')
            print()

        #########SETTING UP THE PLOTTING ENVIRONMENT BASED ON USER CHOICES WITH WIDGETS #############

        fig,ax = plt.subplots(1)
        
        fig.set_figwidth(args['figsize_x'])
        fig.set_figheight(args['figsize_y'])
        
        ax.set_xlim(args['xlim_low'], args['xlim_high'])
        ax.set_ylim(args['ylim_low'], args['ylim_high'])
        

        #plot colors - for now, hardcoded to be standard sherpa colors for concolved model (orange) and data (blue). 
        #unconvolved_color = '#d62728' #red
        unconvolved_color = 'darkorchid' #purple
        convolved_color = '#ff7f0e' #orange to be consistent with sherpa
        data_color = '#1f77b4' #blue to be consistent with sherpa

        #plot font sizes 
        plot_fontsize = 15

        #set the x-axis label based set_analysis result of wavelength or energy
        ax.set_xlabel(xunit, fontsize = plot_fontsize)
        
        #logic for the logbox
        if args['log'] == 'xlog':
            ax.set_xscale('log')
        if args['log'] == 'ylog':
            ax.set_yscale('log')
        if args['log'] == 'loglog':
            ax.set_xscale('log')
            ax.set_yscale('log')
        
        #logic to handle autoscaling of plot -- works magically by overriding xlims--might break someday...
        if args['autoscale'] == 'y':
            ax.autoscale(axis = 'y')
        if args['autoscale'] == 'x':
            ax.autoscale(axis = 'x')
        if args['autoscale'] =='xy':
            ax.autoscale(axis = 'both')
        


        #########PLOTTING THE MODELS/DATA BASED ON THE WIDGET 'plot_type' CHOICE AND HANDLING ERRORS #############


        #check to see if responses are loaded and model is set to source (set_source). All of which must be true to use plot_model to show model convolved with RMF and ARF.

        #error message if user has not loaded something necessary for the plot
        response_error_message = 'ERROR: Convolved model plotting requires a dataset with an ARF and RMF loaded and a model set with set_source().'

        #error message if user tries to plot a convolved model or dataset associated with a different dataset than the default (e.g., get_default_id()) 
        dataset_id_error = 'ERROR: Input model "%s" is not associated via set_source() with dataset_id %s. Please set the dataset_id parameter in notebook_plotter to the dataset associated with this model if you wish to view convolved models or data.' %(model_var.name, dataset_id)

        #using try/excpet here to catch the error if data/responses aren't loaded without killing the plot
        #check ARF
        try:
            is_arf_loaded = get_arf()
        except:
            is_arf_loaded = 'no_arf'

        #check RMF
        try:
            is_rmf_loaded = get_rmf()
        except:
            is_rmf_loaded = 'no_rmf'

        #check set_source()
        try:
            is_src_set = get_source()
        except:
            is_src_set = 'no_src'

        #check if data is loaded
        try:
            is_data_set = get_data()
        except:
            is_data_set = 'no_data'            

        #convert dataset_id to integer type in case the user entered it in string format
        dataset_id_int = int(dataset_id)

        #variable used to check if the model to plot is associated with the ID of the dataset also being plotted
        try:
            source_checker = get_source(dataset_id_int)
        except:
             source_checker = 'source not set'

        #check if the model_var is just a string and if so 
        if type(model_var) == str:
            print('\n\n\n')
            print(response_error_message)
            print('\n\n\n')             

        ##REMOVE>>?
        #grab the default_id that is set for plotting purposes. This way users can use set_default_id to plot a different ID
        #default_dataset = get_default_id()

        #grab the model expression for use in the plot titles
        #title = get_source()
        title_name = model_var.name #this works better than get_source cause the model is always part of the call to the function

        #plot only the unconvolved source model evalulated over the defined energy grid with a user input resolution
        if args['plot_type'] == 'model_unconvolved': #unconvolved model units are in photons/s/cm2/keV 
            ax.plot(emid,model_y, color=unconvolved_color)
            ax.set_ylabel('photons s$^{-1}$ cm$^{-2}$ keV$^{-1}$', fontsize = plot_fontsize)
            ax.set_ylabel(yunit_unconvolved, fontsize = plot_fontsize)
            ax.set_title('Unconvolved Model: %s' %(title_name), fontsize = plot_fontsize)
        
        #plot the source model convolved with the ARF/RMF
        if args['plot_type'] == 'model_convolved':  #convolved model units are in counts/s/keV

            if (is_arf_loaded == 'no_arf') or (is_rmf_loaded == 'no_rmf') or (is_src_set == 'no_src'):
                #print the response error to the screen
                print('\n\n\n')
                print(response_error_message)
                print('\n\n\n')
            elif source_checker != model_var:
                #print the response error to the screen
                print('\n\n\n')
                print(dataset_id_error)
                print('\n\n\n')
            else:
                conv_model = get_model_plot(dataset_id_int)
                ax.plot(conv_model.x, conv_model.y, color = convolved_color)
                ax.set_ylabel(conv_model.ylabel, fontsize = plot_fontsize)
                ax.set_title('Convolved Model: %s' %(title_name), fontsize = plot_fontsize)


        #plot both the unconvolved and convolved source models together with twin axes demonstrating the different units.
        if args['plot_type'] == 'both_models':

            if (is_arf_loaded == 'no_arf') or (is_rmf_loaded == 'no_rmf') or (is_src_set == 'no_src'):
                #print the response error to the screen
                print('\n\n\n')
                print(response_error_message)
                print('\n\n\n')
            elif source_checker != model_var:
                #print the response error to the screen
                print('\n\n\n')
                print(dataset_id_error)
                print('\n\n\n')                
            elif (args['log'] == 'ylog') or (args['log'] == 'loglog'):        
                #need to set up two axes (one for model units and one for convolved units)
                ax.plot(emid,model_y, color = unconvolved_color)
                ax.set_ylabel(yunit_unconvolved, fontsize = plot_fontsize)
                ax.set_title('Unconvolved and Convolved Models')

                conv_model = get_model_plot(dataset_id_int) 
                ax2 = ax.twinx()
                ax2.set_yscale('log')
                ax2.plot(conv_model.x, conv_model.y, color=convolved_color) 
                ax2.set_ylabel(conv_model.ylabel, fontsize = plot_fontsize, color=convolved_color)
                #print('\n hello \n')
            else:        
                #need to set up two axes (one for model units and one for convolved units)
                ax.plot(emid,model_y, color = unconvolved_color)
                ax.set_ylabel(yunit_unconvolved, fontsize = plot_fontsize)
                ax.set_title('Unconvolved and Convolved Models')

                conv_model = get_model_plot(dataset_id_int) 
                ax2 = ax.twinx()
                ax2.plot(conv_model.x, conv_model.y, color=convolved_color) 
                ax2.set_ylabel(conv_model.ylabel, fontsize = plot_fontsize, color=convolved_color)
        
  
        #plot the loaded dataset with the convolved source model. 
        if args['plot_type'] == 'data_and_convolved_model':

            if (is_arf_loaded == 'no_arf') or (is_rmf_loaded == 'no_rmf') or (is_src_set == 'no_src') or (is_data_set == 'no_data'):
                #print the response error to the screen
                print('\n\n\n')
                print(response_error_message)
                print('\n\n\n')
            elif source_checker != model_var:
                #print the response error to the screen
                print('\n\n\n')
                print(dataset_id_error)
                print('\n\n\n')
            else:                            
                pha_data = get_data_plot(dataset_id_int)
                ax.errorbar(pha_data.x, pha_data.y, xerr=pha_data.xerr, yerr=pha_data.yerr, fmt='.', color=data_color)
                ax.set_ylabel(pha_data.ylabel, fontsize = plot_fontsize)
                ax.set_title('Data and Convolved Model')

                conv_model = get_model_plot(dataset_id_int)
                ax.plot(conv_model.x, conv_model.y, color = convolved_color)




############CALLING THE FUNCTIONS NECESSARY TO BUILD THE WIDGET DICTIONARY, ASSEMBLE THE UI BOX AND DISPLAY THE PLOT


    #create the widgets from the user-supplied spectral model and the hard-coded plotting options
    widget_dict = widget_maker(model_var, dataset_id, model_resolution, autoscale, xlim_low, xlim_high, ylim_low, ylim_high, log_axis, plot_type, figsize_x, figsize_x_min, figsize_x_max, figsize_y, figsize_y_min, figsize_y_max, limit_style, widget_step)

    #make the UI object necessary for formatting the widgets in the notebook
    ui = ui_maker(widget_dict)

    #grab the UI keywords and then remove the 'ui_keywords' item from the dictionary since it wont be part of the plot. Note -- Apparently the ui_keywords MUST be removed here and not in the 'model_widget_plotter' function due to how its called with widgets.interactive_output. Be careful to call the ui_maker function BEFORE removing the ui_keywords. This also means that widget_ui_keys variable gets non-explicitly passed to the model_widget_plotter function. 
    widget_ui_keys = widget_dict['ui_keywords'] 
    widget_dict.pop('ui_keywords')        
    

    #generate the interactive plot and update it based on user-chosen values in the notebook_plotter plot.
    out = widgets.interactive_output(model_widget_plotter, widget_dict)
    display(out, ui)
