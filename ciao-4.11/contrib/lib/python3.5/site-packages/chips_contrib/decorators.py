#
#  Copyright (C) 2013  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
#

"""
Provide ChIPS-related decorators. 

* add_chips_undo_buffer

makes sure that any ChIPS commands made within the decorated function
are run within an undo buffer so that

  - the commands are not seen until the routine exits (so that you can make
    multiple calls but they appear at the same time)

  - a single undo call will remove all the changes made in the function

  - any error in the function will reject any change made

Do not make nested calls to this decorator - e.g. the following is not
supported.

  @add_chips_undo_buffer
  def foo():
    ...

  @add_chips_undo_buffer
  def bar():
    ...
    foo()
    ...

* hide_chips_commands

Turns off the window display, runs the commands, and then turns back
on the display. It should not be used with commands that use or create
multiple windows.

If the window.display setting (or preference setting if no window
exists) when the decorated function is called is False/'false', then
the window setting is not set to True at the end of the routine.

Note that undo() and redo() will appear to behave strangely if you use
it after a decorated function, since the first undo call will change
the display back to False, and so subsequent calls to undo will appear
to do nothing, because the changes are not visible on the screen. Use
the info command to see whether objects have been added or deleted.

"""

import pychips
import pychips.advanced

__all__ = ( "add_chips_undo_buffer", 
            "hide_chips_commands" )
    
def add_chips_undo_buffer():
    """A decorator for a function that wraps a ChIPS undo
    buffer around it. That is, the ChIPS commands are 
    aborted on an error, will appear as a single action
    for undo/redo, and all changes will appear at once.

    An example

      @add_chips_undo_buffer()
      def set_labels(xlabel, ylabel, title, size=18):
          set_plot_xlabel(xlabel)
          set_xaxis(['label.size', size])
          set_plot_ylabel(ylabel)
          set_yaxis(['label.size', size])
          set_plot_title(title)
          set_plot(['title.size', size])

    then a call to set_labels() will make all those changes appear
    as if one call had made them - e.g. try

      set_labels('X axis', 'Y axis', 'Plot title')
      undo()
      redo()
      
    """

    def decorator(fn):
        def new_fn(*args, **kwargs):
            pychips.advanced.open_undo_buffer()
            try:
                fn(*args, **kwargs)
            except:
                pychips.advanced.discard_undo_buffer()
                raise
            
            pychips.advanced.close_undo_buffer()

        new_fn.__doc__ = fn.__doc__
        new_fn.__name__ = fn.__name__
        new_fn.__dict__ = fn.__dict__
        new_fn.__module__ = fn.__module__
        return new_fn
            
    return decorator

# TODO: add an argument to say 'this routine calls add_window, so
# change the preference setting'
#
def hide_chips_commands():
    """A decorator for a function that hides the ChIPS commands,
    so that they appear in one go. It does this by turning off the
    window display, calling the function, then restoring the display
    setting.

    It should only be used for a command that draws to a single window;
    it will not work as expected if the routine calls add_window.
    
    If the window display is false before the command then it is left
    as is by this decorator.

    An example

      @hide_chips_commands()
      def set_labels(xlabel, ylabel, title, size=18):
          set_plot_xlabel(xlabel)
          set_xaxis(['label.size', size])
          set_plot_ylabel(ylabel)
          set_yaxis(['label.size', size])
          set_plot_title(title)
          set_plot(['title.size', size])

    then a call to set_labels() will make all those changes appear
    as if one call had made them - e.g. try

      set_labels('X axis', 'Y axis', 'Plot title')

    Note that, unlike the add_chips_undo_buffer decorator, undo and redo
    calls will step through the changes made by the decorator and routine,
    so in this case the first undo call would change the display to False,
    then the next would remove the title.size change, but this is not
    reflected on screen until all the changes made in set_labels have
    been undone.
    """

    def decorator(fn):
        def new_fn(*args, **kwargs):
            try:
                redraw = pychips.advanced.get_window_redraw()
                newwin = False
            except RuntimeError:
                redraw = pychips.get_preference('window.display') == 'true'
                newwin = True
                
            try:
                if redraw:
                    if newwin:
                        pychips.set_preference('window.display', 'false')
                    else:
                        pychips.advanced.set_window_redraw(False)
                        
                fn(*args, **kwargs)
            finally:
                if redraw:
                    try:
                        pychips.advanced.set_window_redraw(True)
                    except RuntimeError:
                        pass

                    if newwin:
                        pychips.set_preference('window.display', 'true')

        new_fn.__doc__ = fn.__doc__
        new_fn.__name__ = fn.__name__
        new_fn.__dict__ = fn.__dict__
        new_fn.__module__ = fn.__module__
        return new_fn
            
    return decorator
            
### End
