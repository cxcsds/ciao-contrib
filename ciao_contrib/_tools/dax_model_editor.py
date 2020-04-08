import sys
from tkinter import *
from tkinter.ttk import *


__all__ = ( "DaxModel", )


class DaxModel(object):
    
    def __init__(self, list_of_model_components):
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
        self.sherpa_model = sherpa_model_component

        ll = LabelFrame(self.get_win(), text=sherpa_model_component.name)
        ll.grid(row=self.get_row(),column=0,columnspan=1, padx=(10,10), pady=(10,10))
        self.next_row()
        
        self.add_column_headers(ll)
        for par in self.sherpa_model.pars:
            self.add_model_parameters(ll,par)
        
    def add_model_parameters(self,lab_frame, par):
        self.model_pars[ par.fullname ] = DaxModelParameter( self,lab_frame, par )
        self.next_row()

    def get_win(self):
        return(self.win)

    def get_row(self):
        return(self.row)
    
    def next_row(self):
        self.row = self.row+1

    def run(self):
        self.win.mainloop()

    def fit(self):
        self.win.destroy()

    def quit(self):
        self.win.destroy()
        sys.exit(1)
        

    def add_buttons(self):

        ff = Frame(self.get_win())
        ff.grid(row=self.get_row(),column=0,pady=(5,5))

        b = Button(ff, text="Fit", command=self.fit)
        b.grid(row=self.get_row(),column=0,columnspan=1,padx=(20,20),pady=(5,5))
        b = Button(ff, text="Cancel", command=self.quit)
        b.grid(row=self.get_row(),column=1,columnspan=1,padx=(20,20),pady=(5,5))



    def add_column_headers(self,lab_frame):
        win = self.get_win()
        row = self.get_row()
        
        for col,txt in enumerate( ["Parameter", "Value", "Frozen?", "Min", "Max", "Units"]):
            l = Label(lab_frame, text=txt)
            l.grid(row=row, column=col)
        
        self.next_row()
        


class DaxModelParameter(object):
    
    
    def __init__(self, parent, label_frame, sherpa_model_parameter):        
        self.sherpa_par = sherpa_model_parameter    
        self.parent = parent
        self.label_frame = label_frame
        self.render_ui()
    
    def _freeze_thaw(self):
        if 1 == self.fz_box.get():
            self.sherpa_par.freeze()
        else:
            self.sherpa_par.thaw()

    def entry_callback(self,keyevt):

        if "Return" == keyevt.keysym:
            setattr( self.sherpa_par, "val",
                float( self.val.get()) )
            self.val.configure(foreground="black")
        else:
            self.val.configure(foreground="red")
    
    def render_ui(self):
        
        row = self.parent.get_row()
        win = self.label_frame
        
        lab = Label( win, text=self.sherpa_par.name, width=10) 
        lab.grid(row=row,column=0,padx=(5,5),pady=2)

        self.val_str = StringVar()  
        self.val = Entry(win, textvariable=self.val_str, 
            foreground="black", width=10)
        self.val.grid(row=row, column=1,padx=(5,5),pady=2)
        self.val.delete(0,END)
        self.val.insert(0,"{}".format(self.sherpa_par.val) )
        self.val.bind("<Key>", self.entry_callback)

        self.fz_box = IntVar()
        if self.sherpa_par.frozen is True:
            self.fz_box.set(1)
        else:
            self.fz_box.set(0)
        fz = Checkbutton(win, text="", variable=self.fz_box, 
            command=self._freeze_thaw)
        fz.grid(row=row,column=2,padx=(5,5),pady=2)
        
        par_min = Label(win, text="{}".format(self.sherpa_par.min), width=10)
        par_min.grid(row=row,column=3,padx=(5,5),pady=2)
        
        par_max = Label(win, text="{}".format(self.sherpa_par.max), width=10)
        par_max.grid(row=row,column=4,padx=(5,5),pady=2)

        par_units = Label(win, text="{}".format(self.sherpa_par.units), width=20)
        par_units.grid(row=row,column=5,padx=(5,5),pady=2)




# ~ import sherpa.astro.ui as sherpa
# ~ sherpa.load_data("out.pi")
# ~ sherpa.group_counts(20)
# ~ sherpa.notice(0.3,7.0)
# ~ sherpa.set_source("xszpowerlw.mdl1 * xswabs.abs1")
# ~ abs1.nH = 0.1399


# ~ DaxModel().run()
