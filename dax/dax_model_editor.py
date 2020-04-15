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

'''Dax Sherpa Model Editor

Provides a simple GUI to edit model parameters
'''

from tkinter import Tk, StringVar, IntVar, END, font, messagebox
from tkinter.ttk import Frame, Button, Label, LabelFrame, Entry
from tkinter.ttk import Checkbutton, Style
import subprocess as sp

__all__ = ("DaxModelEditor", "DaxCancel")


class DaxCancel(Exception):
    "Raised when the Cancel button is pressed"
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class DaxModelEditor():
    '''A simple GUI to edit sherpa model parameters.

    The gui is simple.  Each model component is in it's own
    LabelFrame where each model parameter is then 1 row in the
    UI.

    When the parameter value is edited, the text turns red.  When
    the user hits return, the value is set.

    Note: really no specific sherpa code in here.  Just setting
    an object's .val property (and having freeze|thaw methods).

    '''

    def __init__(self, list_of_model_components, xpa_access_point=None,
                 hide_plot_button=False):
        '''Create a new Tk window for the editor.

        The user supplies a list of sherpa model components.
        '''
        self.xpa = xpa_access_point

        self.win = Tk()
        self.win.title("DAX Sherpa Model Editor")
        sty = Style(self.win)
        sty.theme_use("clam")
        self.row = 0
        self.model_parameters = []
        for mdl in list_of_model_components:
            self.add_model_component(mdl)
        self.add_buttons(hide_plot_button)

    def add_model_component(self, sherpa_model_component):
        '''Create UI elements for model component.

        Each component is a separate LabelFrame.  Each
        model parameter is a row within that frame.
        '''
        self.sherpa_model = sherpa_model_component

        lfrm = LabelFrame(self.get_win(),
                          text=sherpa_model_component.name)
        lfrm.grid(row=self.get_row(), column=0, columnspan=1,
                  padx=(10, 10), pady=(10, 10))
        self.next_row()

        # Repeat column headers in each model component
        self.add_column_headers(lfrm)
        for par in self.sherpa_model.pars:
            mod_par = DaxModelParameter(self, lfrm, par)
            self.model_parameters.append(mod_par)
            self.next_row()

    def add_buttons(self, hide_plot_button):
        '''Add the buttons at the bottom of the UI'''
        myfrm = Frame(self.get_win())
        myfrm.grid(row=self.get_row(), column=0, pady=(5, 5))

        abtn = Button(myfrm, text="Fit", command=self.fit)
        abtn.grid(row=self.get_row(), column=0, columnspan=1,
                  padx=(20, 20), pady=(5, 5))

        if hide_plot_button is False:
            abtn = Button(myfrm, text="Plot", command=self.plot)
            abtn.grid(row=self.get_row(), column=1, columnspan=1,
                      padx=(20, 20), pady=(5, 5))

        abtn = Button(myfrm, text="Reset", command=self.reset)
        abtn.grid(row=self.get_row(), column=2, columnspan=1,
                  padx=(20, 20), pady=(5, 5))

        abtn = Button(myfrm, text="Cancel", command=self.cancel)
        abtn.grid(row=self.get_row(), column=3, columnspan=1,
                  padx=(20, 20), pady=(5, 5))

    def add_column_headers(self, lab_frame):
        '''Add the labels for the columns.  This needs to be in
        sync with the DaxModelParameter.render_ui() method.
        '''
        row = self.get_row()

        stt = Style()
        lfont = stt.lookup("TLabel", "font")
        basefont = font.nametofont(lfont)
        stt.configure("Hdr.TLabel",
                      font=(basefont.cget("family"),
                            basefont.cget("size"),
                            "bold underline"))

        cols = ["Parameter", "Value", "Frozen?", "Min", "Max", "Units"]
        for col, txt in enumerate(cols):
            label = Label(lab_frame, text=txt, style="Hdr.TLabel")
            label.grid(row=row, column=col)
        self.next_row()

    def get_win(self):
        'Return window object'
        return self.win

    def get_row(self):
        'Return the current row in the UI'
        return self.row

    def next_row(self):
        'Increment row in the UI'
        self.row = self.row+1

    def run(self):
        'Start the event loop'
        self.win.mainloop()

    def fit(self):
        '''Stop the event loop.  The expectation is that the next
        command is

        sherpa.fit()'''
        self.win.destroy()

    def reset(self):
        "Restore all values back to initial values"
        for modpar in self.model_parameters:
            modpar.reset()

    def cancel(self):
        '''Stop the event loop and raise a Dax exception'''
        self.win.destroy()
        raise DaxCancel("Cancel Button Pressed")

    @staticmethod
    def xpaget(ds9, cmd):
        "Run xpaget and return string"
        runcmd = ["xpaget", ds9]
        runcmd.extend(cmd.split(" "))
        try:
            out = sp.run(runcmd, check=False, stdout=sp.PIPE).stdout
        except sp.CalledProcessError as sp_err:
            raise RuntimeError("Problem getting '{}'.".format(runcmd) +
                               "Error message: {}".format(str(sp_err)))
        return out.decode().strip()

    def __del__(self):
        """Make sure ds9 plot window is closed"""
        if self.xpa is None:
            return
        plots = self.xpaget(self.xpa, "plot")  # Get a list of plots.
        plots.split(" ")
        if "dax_model_editor" in plots:
            runcmd = ["xpaset", "-p", self.xpa, "plot",
                      "dax_model_editor", "close"]
            sp.run(runcmd, check=False)

    def plot(self):
        '''Plot model with current parameters'''
        import sherpa.astro.ui as sherpa

        if self.xpa is None:
            import matplotlib.pylab as plt
            sherpa.plot_fit()
            plt.show()
            return

        plots = self.xpaget(self.xpa, "plot")  # Get a list of plots.
        plots.split(" ")
        newplot = ("dax_model_editor" not in plots)

        _f = sherpa.get_fit_plot()
        _d = _f.dataplot
        _m = _f.modelplot
        if _d.xerr is None:
            _d.xerr = (_d.x-_d.x)  # zeros

        import dax.dax_plot_utils as dax_plot
        dax_plot.blt_plot_model(self.xpa, _m.x, _m.y,
                           "Dax Model Editor Plot", "X-axis", "Y-axis",
                           new=newplot, winname="dax_model_editor")

        dax_plot.blt_plot_data(self.xpa, _d.x, _d.xerr/2.0, _d.y, _d.yerr)


class DaxModelParameter():
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
        self.initial_value = {'val': self.sherpa_par.val,
                              'min': self.sherpa_par.min,
                              'max': self.sherpa_par.max}
        self.render_ui()

    def _freeze_thaw(self):
        '''ACTION: set the freeze() or thaw() based on the
        checkbox value.'''
        if 1 == self.fz_box.get():
            self.sherpa_par.freeze()
        else:
            self.sherpa_par.thaw()

    @staticmethod
    def __format_val(val):
        'Format parameter values'
        retval = "{:.5g}".format(val)
        return retval

    def reset(self):
        """Reset values to original"""
        for field in ['max', 'min', 'val']:
            to_mod = getattr(self, field)
            to_mod.delete(0, END)
            to_mod.insert(0, self.__format_val(self.initial_value[field]))
            to_mod.configure(foreground="black")
            setattr(self.sherpa_par, field, self.initial_value[field])

    def entry_callback(self, keyevt, field):
        '''ACTION: set the model parameter value when the user
        type <<Return>>.  Otherwise, when user edits value
        it turns red so user knows it hasn't been set yet.

        All values are cast|set to doubles.

        There is no validation in the UI against the min|max
        values.  Sherpa raises an exception if you try to go beyond
        the limits so the color remains red until valid value is
        entered.
        '''
        from sherpa.utils.err import ParameterErr

        # Note: use .char instead of .keysym because Return
        # and Enter on the keypad are different keysym's but both
        # generate CR. This makes sense since can remap keyboard
        # keys -- the action we want is CR, whichever key generates it.

        to_mod = getattr(self, field)

        if '\r' == keyevt.char:
            try:
                fval = float(to_mod.get())
                setattr(self.sherpa_par, field, fval)
                to_mod.configure(foreground="black")
                to_mod.last_value = to_mod.get()
            except (ValueError, ParameterErr) as val_err:
                messagebox.showerror("DAX Model Editor", str(val_err))

        else:
            if to_mod.get() != to_mod.last_value:
                to_mod.configure(foreground="red")

    def render_ui(self):
        '''Render the parameter UI elements and attach bindings'''

        row = self.parent.get_row()
        win = self.label_frame

        # The parameter name
        lab = Label(win, text=self.sherpa_par.name,
                    width=12, anchor="e")
        lab.grid(row=row, column=0, padx=(5, 5), pady=2)

        # The current parameter value
        self.val_str = StringVar()
        self.val = Entry(win, textvariable=self.val_str,
                         foreground="black", width=12, justify="right")
        self.val.grid(row=row, column=1, padx=(5, 5), pady=2)
        self.val.delete(0, END)
        self.val.insert(0, self.__format_val(self.sherpa_par.val))
        self.val.last_value = self.val.get()
        self.val.bind("<KeyRelease>",
                      lambda x: self.entry_callback(x, field='val'))

        # Frozen|Thawed checkbox.  Checked if frozen.
        self.fz_box = IntVar()
        if self.sherpa_par.frozen is True:
            self.fz_box.set(1)
        else:
            self.fz_box.set(0)
        fzbtn = Checkbutton(win, text="", variable=self.fz_box,
                            command=self._freeze_thaw)
        fzbtn.grid(row=row, column=2, padx=(5, 5), pady=2)

        # The min value
        self.min_str = StringVar()
        self.min = Entry(win, textvariable=self.min_str,
                         foreground="black", width=12, justify="right")
        self.min.grid(row=row, column=3, padx=(5, 5), pady=2)
        self.min.delete(0, END)
        self.min.insert(0, self.__format_val(self.sherpa_par.min))
        self.min.last_value = self.min.get()
        self.min.bind("<KeyRelease>",
                      lambda x: self.entry_callback(x, field='min'))

        # The max value
        self.max_str = StringVar()
        self.max = Entry(win, textvariable=self.max_str,
                         foreground="black", width=12, justify="right")
        self.max.grid(row=row, column=4, padx=(5, 5), pady=2)
        self.max.delete(0, END)
        self.max.insert(0, self.__format_val(self.sherpa_par.max))
        self.max.last_value = self.max.get()
        self.max.bind("<KeyRelease>",
                      lambda x: self.entry_callback(x, field='max'))

        # The units of the parameter
        par_units = Label(win, text="{}".format(self.sherpa_par.units),
                          width=20, anchor="e")
        par_units.grid(row=row, column=5, padx=(5, 5), pady=2)


def test_dax_if():
    '''Test script'''
    import sherpa.astro.ui as sherpa
    sherpa.load_arrays(1, [1, 2, 3], [4, 5, 6], sherpa.Data1D)
    sherpa.set_source("polynom1d.ply")
    # DaxModelEditor([ply], "ds9").run()
    DaxModelEditor([ply]).run()


if __name__ == '__main__':
    test_dax_if()
