#  Copyright (C) 2020  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



import sys
from tkinter import *
from tkinter.ttk import *


__all__ = ( "DaxModelEditor", )


class DaxModelEditor(object):
    '''A simple GUI to edit sherpa model parameters.
    
    The gui is simple.  Each model component is in it's own
    LabelFrame where each model parameter is then 1 row in the 
    UI.
    
    When the parameter value is edited, the text turns red.  When
    the user hits return, the value is set.
    
    Note: really no specific sherpa code in here.  Just setting
    an object's .val property (and having freeze|thaw methods).
    
    '''


    def __init__(self, list_of_model_components):
        '''Create a new Tk window for the editor.  
        
        The use supplies a list of sherpa model components.
        '''

        self.win = Tk()
        self.win.title("DAX Sherpa Model Editor")
        s = Style(self.win)
        s.theme_use("clam")
        self.row = 0
        self.model_pars = {}
        for mdl in list_of_model_components:
            self.add_model_component(mdl)
        self.add_buttons()
                

    def add_model_component(self,sherpa_model_component):       
        '''Create UI elements for model component.
        
        Each component is a separate LabelFrame.  Each
        model parameter is a row within that frame.
        '''
        self.sherpa_model = sherpa_model_component

        ll = LabelFrame(self.get_win(), text=sherpa_model_component.name)
        ll.grid(row=self.get_row(),column=0,columnspan=1, 
            padx=(10,10), pady=(10,10))
        self.next_row()
        
        # Repeat column headers in each model component
        self.add_column_headers(ll)
        for par in self.sherpa_model.pars:
            self.add_model_parameters(ll,par)
        

    def add_model_parameters(self,lab_frame, par):
        '''Not sure this is actually needed to be written like this.
        
        We dont' actually use the .model_pars values after this.
        Just not sure if there's 
        '''
        self.model_pars[ par.fullname ] = DaxModelParameter( self,lab_frame, par )
        self.next_row()


    def get_win(self):
        'Return window object'
        return(self.win)

    def get_row(self):
        'Return the current row in the UI'
        return(self.row)
    
    def next_row(self):
        'Increment row in the UI'
        self.row = self.row+1

    def run(self):
        'Start the event loop'
        self.win.mainloop()

    def fit(self):
        '''Stop the event loop.  The expectation is that the next command
        is sherpa.fit()'''
        self.win.destroy()

    def quit(self):
        '''Stop the event loop and exit. I don't like hard-exits 
        but here it is.'''
        self.win.destroy()
        sys.exit(1)
        

    def add_buttons(self):
        '''Add the buttons at the bottom of the UI'''
        ff = Frame(self.get_win())
        ff.grid(row=self.get_row(),column=0,pady=(5,5))

        b = Button(ff, text="Fit", command=self.fit)
        b.grid(row=self.get_row(),column=0,columnspan=1,padx=(20,20),pady=(5,5))
        b = Button(ff, text="Cancel", command=self.quit)
        b.grid(row=self.get_row(),column=1,columnspan=1,padx=(20,20),pady=(5,5))



    def add_column_headers(self,lab_frame):
        '''Add the labels for the columns.  This needs to be in 
        sync with the DaxModelParameter.render_ui() method.
        '''
        win = self.get_win()
        row = self.get_row()
        
        for col,txt in enumerate( ["Parameter", "Value", "Frozen?", "Min", "Max", "Units"]):
            l = Label(lab_frame, text=txt)
            l.grid(row=row, column=col)        
        self.next_row()
        


class DaxModelParameter(object):
    '''The UI elements and logic to set model parameter values.
    
    For this application; all model parameters are assumed to be
    floats (or ints cast to floats). Strings and Logicals need not
    apply.    
    '''
    
    def __init__(self, parent, label_frame, sherpa_model_parameter):        
        '''Create model parameter UI element'''
        self.sherpa_par = sherpa_model_parameter    
        self.parent = parent
        self.label_frame = label_frame
        self.render_ui()
    
    def _freeze_thaw(self):
        '''ACTION: set the freeze() or thaw() based on the 
        checkbox value.'''
        if 1 == self.fz_box.get():
            self.sherpa_par.freeze()
        else:
            self.sherpa_par.thaw()

    def entry_callback(self,keyevt):
        '''ACTION: set the model parameter value when the user
        type <<Return>>.  Otherwise, when user edits value 
        it turns red so user knows it hasn't been set yet.
        
        All values are cast|set to doubles.
        
        There is no validation in the UI against the min|max 
        values.  Sherpa raises an exception if you try to go beyond
        the limits so the color remains red until valid value is 
        entered.        
        '''
        if "Return" == keyevt.keysym:
            setattr( self.sherpa_par, "val",
                float( self.val.get()) )
            self.val.configure(foreground="black")
        else:
            self.val.configure(foreground="red")
    

    def render_ui(self):
        '''Render the parameter UI elements and attach bindings'''
        
        row = self.parent.get_row()
        win = self.label_frame

        # The parameter name
        lab = Label( win, text=self.sherpa_par.name, width=10) 
        lab.grid(row=row,column=0,padx=(5,5),pady=2)

        # The current parameter value
        self.val_str = StringVar()  
        self.val = Entry(win, textvariable=self.val_str, 
            foreground="black", width=10)
        self.val.grid(row=row, column=1,padx=(5,5),pady=2)
        self.val.delete(0,END)
        self.val.insert(0,"{}".format(self.sherpa_par.val) )
        self.val.bind("<Key>", self.entry_callback)

        # Frozen|Thawed checkbox.  Checked if frozen.
        self.fz_box = IntVar()
        if self.sherpa_par.frozen is True:
            self.fz_box.set(1)
        else:
            self.fz_box.set(0)
        fz = Checkbutton(win, text="", variable=self.fz_box, 
            command=self._freeze_thaw)
        fz.grid(row=row,column=2,padx=(5,5),pady=2)
        
        # The min value
        # TODO: Lock/UnLock limits for editing
        par_min = Label(win, text="{}".format(self.sherpa_par.min), width=10)
        par_min.grid(row=row,column=3,padx=(5,5),pady=2)

        # The max value
        par_max = Label(win, text="{}".format(self.sherpa_par.max), width=10)
        par_max.grid(row=row,column=4,padx=(5,5),pady=2)

        # The units of the parameter
        par_units = Label(win, text="{}".format(self.sherpa_par.units), width=20)
        par_units.grid(row=row,column=5,padx=(5,5),pady=2)




# ~ import sherpa.astro.ui as sherpa
# ~ sherpa.load_data("out.pi")
# ~ sherpa.group_counts(20)
# ~ sherpa.notice(0.3,7.0)
# ~ sherpa.set_source("xszpowerlw.mdl1 * xswabs.abs1")
# ~ abs1.nH = 0.1399
# ~ DaxModel([mdl1,abs1]).run()
