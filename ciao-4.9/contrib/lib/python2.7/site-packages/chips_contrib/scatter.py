#
#  Copyright (C) 2014, 2015, 2016
#            Smithsonian Astrophysical Observatory
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

"""Create scatter plots for a set of variables, which can be read from
a table or 2D image, or set explicitly.

Based on examples like

  http://benjiec.github.io/scatter-matrix/demo/demo.html
  http://www.statmethods.net/graphs/scatterplot.html

There are four routines:

  - scatterplots(), to either create a set of plots or add to
    an existing set of plots

  - scatterlog(), to change one or more of the columns/rows to log scale
    in a set of plots

  - scatterlin(), to change one or more of the columns/rows to a
    linear scale in a set of plots.

  - scatterlimits(), to change the limits of a column/row

The long names at the IPython prompt if you import the whole module, e.g.

  >>> from chips_contrib.scatter import *

There are also shorter names - splots(), slog(), slin(), and slimits() -
for qualified use:

  >>> from chips_contrib import scatter
  >>> scatter.splots('data.fits')
  >>> scatter.slog(['lx'])
  >>> scatter.slimits('lx', 1e-13, 1e-15)

Example
-------

  >>> add_window(9, 9, 'inches')
  >>> scatterplots("src.fits[cols x,y,fx,lx,hr]")
  >>> scatterplots("src.fits[z>0.2][cols x,y,fx,lx,hr]", overplot=True,
                   color='orange')
  >>> scatterlog(["fx", "lx"])
  >>> scatterlimits("lx", 1e-13, 2e-15)

"""

# TODO:
#  *) There are at least two conversions for variable names
#       .replace(' ', '_')
#       .replace(' ', '')
#     This should be consolidated.
#

import six

import numpy as np

import pycrates
import pychips

from ciao_contrib.logger_wrapper import initialize_module_logger
from chips_contrib.decorators import add_chips_undo_buffer

logger = initialize_module_logger("chips.scatter")

v2 = logger.verbose2
v3 = logger.verbose3
v4 = logger.verbose4

__all__ = ("scatterplots", "scatterlog", "scatterlin", "scatterlimits")


def _extract_init():
    "Return an empty structure for use by the _extract... routines"

    return {'names': [], 'values': {}, 'units': {}}


def _extract_validate(out):
    "Raise an error if there is a problem"

    if len(out['names']) == 0:
        raise ValueError("There is no numeric data to display!")

    # The values elements are 1D NumPy arrays. Note that
    # _extract_data_array normalizes all the variables to the
    # same size, so this is mainly a check for the other methods
    # (which could be adjusted to do the same), or the
    # code in _extract_data_array could be removed.
    #
    nrows = [v.size for v in six.itervalues(out['values'])]
    nrows = np.unique(nrows)
    if nrows[0] == 0:
        raise ValueError("No data to plot, all variables are empty.")
    elif len(nrows) != 1:
        raise ValueError("Variables are unequal in length: {}".format(nrows))

    # We need unique variable names for the plots, without spaces,
    # since ChIPS ids can not include spaces.
    #
    # The naming scheme to avoid overlaps is simple but not ideal.
    # At present this allows the code to deal with variables that have
    # the same name bar spaces.
    #
    out['_plotnames'] = {}
    for name in out['names']:
        cname = name.replace(' ', '_')
        while cname in out['_plotnames']:
            cname += "1"

        v3("Storing plot name {} -> {}".format(name, cname))
        out['_plotnames'][name] = cname


def _extract_add_variable(out, name, values, unit=''):
    """Add name,values,unit to out (return value of _extract_init).

    Does some simple validation (e.g. name is unique and values is
    a 1D array). values must be a numpy array
    """

    v3("Adding variable: {}".format(name))
    if name in out['names']:
        raise ValueError("Found multiple versions of the variable {}".format(name))

    if values.ndim != 1:
        raise ValueError("The variable {} must be 1D; sent {}D!".format(name, values.ndim))

    out['names'].append(name)
    out['values'][name] = values
    if unit != '':
        out['units'][name] = unit


def _extract_data_tablecrate(cr):
    "cr is a table crate; we copy the numeric values"

    out = _extract_init()
    v3("Extracting data from table with ncol={} nrows={}".format(
        cr.get_ncols(), cr.get_nrows()))

    names = cr.get_colnames()
    for name in names:
        data = cr.get_column(name)
        try:
            data.values + 0
        except TypeError:
            continue

        _extract_add_variable(out, name, data.values.copy(), unit=data.unit)

    _extract_validate(out)
    return out


def _extract_data_dict(obj):
    "cr is a dictionary-like object; we copy the numeric values"

    out = _extract_init()
    v3("Extracting data from a dictionary with nkey={}".format(len(obj)))

    for (name, data) in six.iteritems(obj):
        try:
            data + 0
        except TypeError:
            continue

        _extract_add_variable(out, name, data.copy())

    _extract_validate(out)
    return out


def _extract_data_image(img, unit=''):
    """Given a 2D array, extract the variables from the columns. The
    variable names are x0 to x<nx-1>, where nx is the number of
    columns.  The variable units are given in the unit argument (''
    means no units).
    """

    out = _extract_init()

    (ny, nx) = img.shape
    v3("Extracting variables from nx={} ny={} image".format(nx, ny))
    for i in range(nx):
        name = "x{}".format(i)
        _extract_add_variable(out, name, img[:, i].copy(), unit=unit)

    _extract_validate(out)
    return out


def _extract_data_imagecrate(cr):
    """cr is an image crate; split on columns. we copy the values.

    The input image must contain 2 dimensions with a size > 1.
    """

    sh = cr.get_shape()
    dims = []
    for (i, d) in zip(range(len(sh)), sh):
        if d > 1:
            dims.append(i)

    if len(dims) == 0:
        raise ValueError("The crate {} has no interesting dimensions!".format(cr.name))

    if len(dims) < 2:
        raise ValueError("The crate {} only has 1 interesting dimension!".format(cr.name))

    if len(dims) > 2:
        raise ValueError("The crate {} has more than 2 ({}) interesting dimensions!".format(cr.name, len(dims)))

    nx = sh[dims[1]]
    ny = sh[dims[0]]

    img = cr.get_image()
    ivals = img.values.copy().flatten().reshape(ny, nx)

    return _extract_data_image(ivals, unit=img.unit)


# TODO: should be able to provide a list of variable names
# TODO: should be able to give a rec array?
# TODO: use np.nan rather than 0 for the missing value (for floats at least)
#
def _extract_data_array(ary, missing=0):
    """Assume a 2D sequence for ary, that is ary[0] is a
    1D sequence. The elements of ary (i.e. ary[0] to ary[n-1])
    are the variables - e.g.

      _extract_data_array([[1,2,3], [10,20,30]])

    has two variables, [1,2,3] and [10,20,30]. This is different
    to how image arrays are treated, since

      img = np.asarray([[1,2,3], [10,20,30]])
      _extract_data_image(img)

    would return 3 variables, each with two elements:
       [1,10], [2,20, and [3,30].

    Need to work out if this all makes sense.

    The variables are converted to the same length, the maximum
    column length (missing values are set to missing).
    Non-numeric and multi-dimensional elements are ignored.

    """

    ary2 = []
    ny = None
    for i in range(len(ary)):
        ii = np.asarray(ary[i])
        if ii.ndim != 1:
            continue

        try:
            ii + 0
        except TypeError:
            continue

        ary2.append(ii)
        if ny is None or ii.size > ny:
            ny = ii.size

    nx = len(ary2)
    if nx < 2:
        raise ValueError("There must be at least 2 numeric 1D variables, found {}.".format(nx))

    for i in range(nx):
        col = ary2[i]
        if col.size < ny:
            ary2[i] = np.resize(ary2[i], ny)
            ary2[i][ny:] = missing

    return _extract_data_image(np.asarray(ary2).T)


def _extract_data_file(filename):
    "Read in data from a file"

    v3("Reading data from: {}".format(filename))
    cr = pycrates.read_file(filename)
    try:
        cr.get_colnames()
        return _extract_data_tablecrate(cr)

    except AttributeError:
        return _extract_data_imagecrate(cr)


def _extract_data(arg):
    """arg can be a crate, file name, dictionary, or array of columns."""

    if isinstance(arg, six.string_types):
        v3("Assuming argument is a file name")
        return _extract_data_file(arg)

    try:
        six.iteritems(arg)
        v3("Assuming argument is a dictionary")
        return _extract_data_dict(arg)
    except AttributeError:
        pass

    try:
        arg.get_colnames()
        v3("Assuming argument is a table crate")
        return _extract_data_tablecrate(arg)

    except AttributeError:
        pass

    try:
        arg.get_image()
        v3("Assuming argument is an image crate")
        return _extract_data_imagecrate(arg)

    except AttributeError:
        pass

    v3("Assuming argument is an array of variables")
    return _extract_data_array(arg)


# Should this replace ' ' by '_' instead?
def _col_to_name(colname):
    """Convert a variable name into a form used in this routine
    (to label a plot).
    """

    return colname.replace(' ', '')


def _plot_name(xcol, ycol):
    "Return the plot for the given columns."
    return "plot_{}_{}".format(_col_to_name(xcol),
                               _col_to_name(ycol))


def _pairs_skip(names, xname, yname, style):
    """Returns True if this plot is to be skipped, due
    to the style setting (which should be 'all', 'upper',
    or 'lower').
    """

    if style == 'all':
        return False
    else:
        xi = names.index(xname)
        yi = names.index(yname)
        return ((style == 'upper') and (xi < yi)) or \
            ((style == 'lower') and (xi > yi))


def _first_entry_col(names, xi, style):
    """Return the name of the first "valid" row in column
    number xi (xi starts at 1), where the rows are called
    names and the plot style is
    'all', 'upper', or 'lower'.

    None is returned if the selected entry is the last valid
    item in the column.
    """

    nrows = len(names)
    assert nrows > 1, 'expect to plot at least 2 variables'

    if style == 'lower':
        i = xi

    else:
        if xi == 1:
            i = 1
        else:
            i = 0

    if i + 1 >= nrows:
        i = None

    if i is None:
        return None
    else:
        return names[i]


def _first_entry_row(names, yi, style):
    """Return the name of the first "valid" column in row
    number yi (yi starts at 1), where the columns are called
    names and the plot style is
    'all', 'upper', or 'lower'.

    None is returned if the selected entry is the last valid
    item in the row.
    """

    ncols = len(names)
    assert ncols > 1, 'expect to plot at least 2 variables'

    if style == 'upper':
        i = yi

    else:
        if yi == 1:
            i = 1
        else:
            i = 0

    if i + 1 >= ncols:
        i = None

    if i is None:
        return None
    else:
        return names[i]


def _get_plot_names():
    """Return the list of plot names in the current frame,
    or None."""

    info = pychips.info()
    if info is None:
        return None

    def get_bracketed(s):
        lpos = s.find('[') + 1
        rpos = s.find(']', lpos)
        return s[lpos:rpos]

    return [get_bracketed(l)
            for l in info.split('\n')
            if l.lstrip().startswith('Plot [')]


def _get_axis_names():
    """Guess the column names from the output of info();
    this is only going to work if the plots in the current
    frame were created by scatterplots().

    Returns None if no axis names can be found.
    """

    # look for the a_a pairs, and assumes that the
    # plots have not been re-arranged
    pnames = _get_plot_names()
    if pnames is None:
        v3("No plots found")
        return None

    pnames = [p[5:] for p in pnames]
    nplots = len(pnames)
    if nplots == 0:
        v3("No plots found")
        return None  # should not be possible given _get_plot_names

    ncols = int(np.sqrt(nplots))
    v3("Found {} variables in scatter plot".format(ncols))

    # I have seen this condition violated, but not clear when (the
    # typo in format obscured the situations)
    if ncols * ncols != nplots:
        v2("Expected the number of plots to be a square number, but found {}".format(nplots))
        return None

    pname = pnames[0]
    colnames = [pname[:len(pname) // 2]]
    if pname != "{0}_{0}".format(colnames[0]):
        v2("Expected first plot name to be plot_<colname>_<colname> but sent ...{}".format(pname))
        return None

    clen = len(colnames[0]) + 1
    for i in range(1, ncols):
        pname = pnames[i]
        v3("Looking at plot {}".format(pname))
        if not pname.endswith("_" + colnames[0]):
            v2("Expected plot to end with _{} but found ...{}".format(colnames[0], pname))
            return None

        colnames.append(pname[:len(pname) - clen])

    return colnames


def _match_axis_names(usernames):
    """Given a set of axis names from the user (an array of name
    or integer values), return an array of those axes which are
    found in the existing plot. The return value is a tuple of
    (user value, column name as used in the plot).

    If there are no matches None is returned.
    """

    v3("Matching user names to axis names from the plots")
    anames = _get_axis_names()
    alower = [a.lower() for a in anames]
    out = []
    for n in usernames:
        idx = None
        try:
            idx = alower.index(n.lower())

        except ValueError:
            v3("Skipping variable {}".format(n))

        except AttributeError:
            try:
                if int(n) == n:
                    idx = n
            except ValueError:
                v3("Unable to match variable {} by name or index".format(n))

        if idx is not None:
            try:
                v3("Found variable for {} -> {}".format(n, anames[idx]))
                out.append((n, anames[idx]))
            except IndexError:
                v3("Invalid variable index {}".format(idx))

    if len(out) == 0:
        v3("No matching axes found")
        return None
    else:
        v3("Found {} matching axes.".format(len(out)))
        return out


def _pairs_axes(names, xname, xi, yname, yi, style, plotname, axname, ayname):
    """Set the axes for the given plot
    (xname/xi, yname/yi) given the plot style
    (one of 'all', 'upper', 'lower').
    """

    v3("Adding plot of {} vs {} style={}".format(xname, yname, style))

    axopts = {'majortick.style': 'outside',
              'minortick.style': 'outside',
              'majortick.length': 6,
              'ticklabel.offset': 10,
              'ticklabel.size': 14,
              'ticklabel.visible': False,
              'minortick.visible': False}

    axonopts = {'ticklabel.visible': True}

    pychips.add_axis(pychips.XY_AXIS, 0, 0, 1)
    pychips.set_axis('all', axopts)

    # The choice of the axis settings depends on the chosen style: if
    # it is all then we can place axis labels at alternating up/down
    # or left/right locations on the column or row; for the triangular
    # forms we just place everything on the same edge (we could place
    # them on the plots bordering the diagonal, but then will likely
    # overlap with the labels in those plots).
    #
    # Since want this to apply to the borders too can not just add
    # axopts to the end of the add_axis call.
    #
    # Note that the move_axis call - in CIAO 4.6 - can cause the
    # minortick.visible settings of borders to reset to True, so we
    # add an explicit re-set. This is bug #13800. Could this be
    # causing the problem with undo leading to the border visibility
    # changing seen in 4.7?
    #
    # This logic also handles the case when ncols is odd, so we have
    # added axes to the last (bottom-right) plot, which is a "label"
    # plot (i.e. no data) when style=all; for the other styles we
    # label all the axes along the edge - i.e. no alternating,
    # although perhaps could do so, if we include the label plots
    # (i.e.  those on the diagonal).
    #
    ncols = len(names)
    if yi == 1 and style != 'lower':
        if xi % 2 == 0 or style == 'upper':
            pychips.set_axis(axname, axonopts)
            pychips.move_axis(axname, 0, 1)
            pychips.set_axis('all', ['minortick.visible', False])

    elif yi == ncols:
        if xi % 2 == 1 or style == 'lower':
            pychips.set_axis(axname, axonopts)

    if xi == 1 and style != 'upper':
        if yi % 2 == 0 or style == 'lower':
            pychips.set_axis(ayname, axonopts)

    elif xi == ncols:
        if yi % 2 == 1 or style == 'upper':
            pychips.set_axis(ayname, axonopts)
            pychips.move_axis(ayname, 1, 0)
            pychips.set_axis('all', ['minortick.visible', False])

    inLastPlot = ncols % 2 == 1 and xi == ncols and yi == ncols
    if inLastPlot and style != 'all':
        assert style in ['upper', 'lower'], "Unexpected style={}".format(style)
        axid = pychips.ChipsId()
        if style == 'upper':
            axid.yaxis = ayname
        else:
            axid.xaxis = axname

        pychips.delete_axis(axid)

    # We already know the indexes, so the .index done by _pairs_skip
    # is wasteful, but simpler code wins out (and it's not as if it's
    # a huge time sink here anyway)
    isValid = not _pairs_skip(names, xname, yname, style)

    # Bind the axes together
    #
    # There is some unnescessary work that we could resolve; in
    # particular we know that the first entry in each row/column does
    # not need to be bound, but the following is simpler to code.
    #
    # Added complexity is dealing with the fact that we do not want
    # both axes bound if the number of variables is odd, this is the
    # last plot, and style!='all'.
    #
    if isValid:

        # We do not need to check for whether inLastPlot is True and
        # style != 'all' here (i.e. whether an axis has been deleted),
        # since name0 will be None in this case, so the bind will not
        # happen.
        #
        name0 = _first_entry_col(names, xi, style)
        if name0 is not None:
            pname = _plot_name(xname, name0)
            if pname != plotname:
                pychips.bind_axes(pname, axname, plotname, axname)

        name0 = _first_entry_row(names, yi, style)
        if name0 is not None:
            pname = _plot_name(name0, yname)
            if pname != plotname:
                pychips.bind_axes(pname, ayname, plotname, ayname)


def _pairs_make_plots(names, style='all', gap=0.05, margin=0.15):
    """Make all the plots and axes.

    gap is the spacing between plots, in both x and y,
    and is given as a fraction of the available width/height.

    margin is the spacing to use from the edge of the frame
    to the plot edge; this overrides the plot preference settings.

    style refers whether all plots, upper right, or lower left
    are created (in all cases the diagonal is excluded).
    """

    # popts = { 'style': 'boxed',
    popts = {'style': 'closed',
             'leftmargin': margin,
             'rightmargin': margin,
             'topmargin': margin,
             'bottommargin': margin}

    prefs = pychips.get_preferences()
    ax1 = prefs.axis.x.stem + "1"
    ay1 = prefs.axis.y.stem + "1"

    # Even though we may not need all the plots, we have to create them
    # so that we can use the grid command to arrange the layout.
    # Perhaps we should just place the plots ourselves?
    #
    ncols = len(names)
    ids = range(1, ncols + 1)
    v2("Creating plots for {} variables with style={}".format(ncols, style))
    for (yi, yname) in zip(ids, names):
        for (xi, xname) in zip(ids, names):
            v2("Plot: x={}/{} y={}/{}".format(xname, xi, yname, yi))

            popts['id'] = _plot_name(xname, yname)
            pychips.add_plot(popts)

            if xi == yi:
                v2(" -- diagonal row plot")
                pychips.set_plot(['style', 'open'])

                # For an odd number of variables, we need to add in the
                # axes if this is the last plot and style=all
                if ncols % 2 == 0 or xi != ncols or yi != ncols or \
                   style != 'all':
                    continue

                v2("    -- adding in axes to the last plot (odd number of variables)")

            elif _pairs_skip(names, xname, yname, style):
                v2(" -- skipping plot because of style={}".format(style))
                pychips.hide_plot()
                continue

            _pairs_axes(names, xname, xi, yname, yi, style, popts['id'],
                        ax1, ay1)

    pychips.grid_objects(ncols, ncols, gap, gap)


def _pairs_plot(colinfo, xname, yname,
                style='all',
                symbol='circle',
                color='blue',
                size=2,
                fill=True,
                ticks=4):
    """Plot up variable xname against yname.
    """

    v4("In _pairs_plot for x={} y={}".format(xname, yname))
    if _pairs_skip(colinfo['names'], xname, yname, style):
        return

    pychips.current_plot(_plot_name(xname, yname))

    if xname == yname:
        lopts = {'halign': 0.5, 'valign': 0.5,
                 'size': 16, 'coordsys': pychips.PLOT_NORM}
        pychips.add_label(0.5, 0.5,
                          xname.replace('_', '\\_'),
                          lopts)
        try:
            lopts['size'] = 14
            lopts['valign'] = 0
            pychips.add_label(0.5, 0.1,
                              "(" + colinfo['units'][xname] + ")",
                              lopts)
        except KeyError:
            pass

        return

    x = colinfo['values'][xname]
    y = colinfo['values'][yname]
    copts = {'line.style': 'noline',
             'symbol.style': symbol,
             'symbol.size': size,
             'symbol.fill': fill,
             '*.color': color}
    pychips.add_curve(x, y, copts)

    if ticks is not None:
        pychips.set_axis(['majortick.count', ticks])


def _pairs_overplot(colinfo, xname, yname,
                    pxname, pyname,
                    symbol='circle',
                    color='blue',
                    size=2,
                    fill=True):
    """Overplot variable xname against yname if there is
    an existing plot.
    """

    if xname == yname:
        return

    v4("In _pairs_overplot for x={} y={} px={} py={}".format(xname,
                                                             yname,
                                                             pxname,
                                                             pyname))

    pname = _plot_name(xname, yname)
    try:
        pychips.current_plot(pname)
        pychips.get_xaxis()
        pychips.get_yaxis()
    except RuntimeError:
        return

    x = colinfo['values'][xname]
    y = colinfo['values'][yname]
    copts = {'line.style': 'noline',
             'symbol.style': symbol,
             'symbol.size': size,
             'symbol.fill': fill,
             '*.color': color}
    pychips.add_curve(x, y, copts)


def _scatterplots_new(colinfo,
                      style='all',
                      margin=0.15,
                      gap=0.05,
                      symbol='circle',
                      color='blue',
                      size=2,
                      fill=True,
                      ticks=4,
                      overplot=False,
                      ):
    """Create a new set of plots and add the data.
    """

    names = colinfo['names']
    pychips.erase()
    _pairs_make_plots(names, margin=margin, gap=gap, style=style)
    for yname in names:
        for xname in names:
            _pairs_plot(colinfo, xname, yname, style=style,
                        symbol=symbol, color=color,
                        size=size, fill=fill, ticks=ticks)


def _scatterplots_add(colinfo,
                      symbol='circle',
                      color='blue',
                      size=2,
                      fill=True):
    """Add to the existing plots
    """

    # what are the common names?
    #
    # TODO: use _match_axis_names instead of the loop below
    axnames = _get_axis_names()
    laxnames = [n.lower() for n in axnames]

    names = colinfo['names']

    # I have forgotten exactly what transformations I am applying to
    # variable names, so do we need to go to this much bother to match
    # variable names to the name used in the plots? It does seem like
    # there is both repetition and the possibility of confusion.
    #
    common = []
    for n in names:
        try:
            idx = laxnames.index(n.lower())
        except ValueError:
            continue

        common.append((n, axnames[idx]))

    if len(common) == 0:
        v2("No variables match the existing plot!")
        return

    for (cyname, pyname) in common:
        for (cxname, pxname) in common:
            _pairs_overplot(colinfo, cxname, cyname,
                            pxname, pyname,
                            symbol=symbol, color=color,
                            size=size, fill=fill)


@add_chips_undo_buffer()
def _scatterplots(colinfo,
                  style='all',
                  margin=0.15,
                  gap=0.05,
                  symbol='circle',
                  color='blue',
                  size=2,
                  fill=True,
                  ticks=4,
                  overplot=False):
    """Plot the data returned by _extract_data.
    """

    # can _scatterplots_new be split up into plot creation and then
    # data addition, to share code with _scatterplots_add?
    if overplot:
        _scatterplots_add(colinfo,
                          symbol=symbol,
                          color=color,
                          size=size,
                          fill=fill)
    else:
        _scatterplots_new(colinfo,
                          style=style,
                          margin=margin,
                          gap=gap,
                          symbol=symbol,
                          color=color,
                          size=size,
                          fill=fill,
                          ticks=ticks)


def scatterplots(data,
                 style='all',
                 margin=0.15,
                 gap=0.05,
                 symbol='circle',
                 color='blue',
                 size=2,
                 fill=True,
                 ticks=4,
                 overplot=False):
    """Create scatter plots for all pairs of numeric data, where data is
    one of: file name, crate, list of variables, dictionary (keys are
    names, values are the variable data).

    Parameters
    ----------
    data :
        The data argument can be one of:
        a filename, supporting CIAO Data Model syntax;
        a Crate;
        a dictionary (keys are the variable names, values are the variable
        values);
        a sequence of columns - e.g. a tuple or list - where the
        variable names are set to "x0", "x1", ...;
        or a 2D image, which is treated as a selection of columns (so a
        nx by ny image has nx variables, each of length ny); the
        variables are named "x0", "x1", ....
        Non-numeric and non-scalar values are ignored.
    style : one of 'all', 'upper', 'lower'
        Create a n by n grid of plots ('all'), just the upper-right
        plots ('upper'), or lower-left plots ('lower'). In all cases
        the diagonal plots are created: these are used to label the
        columns and rows.
    margin : float (0 to 1 inclusive)
        The spacing from the frame edge to the plot edge.
    gap : float (0 to 1 inclusive)
        The horizontal and vertical spacing between the plots.
    symbol : string
        The ChIPS symbol name to use for the points.
    color : string or integer (0x000000 to 0xFFFFFF)
        The ChIPS color name.
    size : integer (1 to 100 inclusive)
        The ChIPS symbol size.
    fill : boolean
        Is the symbol drawn filled?
    ticks : integer (2 or greater) or None
        If not None, the number of tick marks to display on each
        axis, which sets the ChIPS majortick.mode to "count" for each
        axis. If None then the default mode ("limits") is used.
    overplot : boolean
        If False then a new set of plots is created in the current
        frame. If True then the style, margin, gap, and ticks
        arguments are ignired and the data is added to existing plots,
        which are assumed to have been created by an earlier call to
        scatterplots(). Any unknown variables are ignored, and the
        number of variabless can be less than the original plot (e.g. to
        highlight only a subset of plots).

    Examples
    --------

    Plotting data from a file:

      >>> scatterplots('tbl.fits')
      >>> scatterplots('tbl.fits[hr>0.2][cols rate1,rate2,rate3]')

    Plotting data from a Crate:

      >>> cr = read_file('srcs.csv[opt skip=","]')
      >>> scatterplots(cr)

    Plotting data from NumPy arrays or Python lists:

    In the following x, y, and z are 1D lists or NumPy arrays.

      >>> scatterplots((x, y, z))
      >>> scatterplots([x, y, z])

    Plotting an image:

    Here img is a nx by ny pixel image, so img.shape == (ny,nx)) which
    is taken to be nx variables

      >>> scatterplots(img)

    Plotting from a CSV file:

    If we have - taken from
    http://en.wikipedia.org/wiki/Iris_flower_data_set - the following
    file

      % head data/iris.csv
      species,sepal length,sepal width,petal length,petal width
      setosa,5.1,3.5,1.4,0.2
      setosa,4.9,3,1.4,0.2
      setosa,4.7,3.2,1.3,0.2
      setosa,4.6,3.1,1.5,0.2
      setosa,5,3.6,1.4,0.2
      setosa,5.4,3.9,1.7,0.4
      setosa,4.6,3.4,1.4,0.3
      setosa,5,3.4,1.5,0.2
      setosa,4.4,2.9,1.4,0.2

    then we can read this in using the ASCII support in the CIAO Data
    Model, described in http://cxc.harvard.edu/ciao/ahelp/dmascii.html

      >>> add_window(8, 8, 'inches')
      >>> scatterplots('data/iris.csv[opt skip=1,sep=","]')

    where the skip=1 option is needed to avoid the header line
    (otherwise it will read in the strings and assume every column is
    a string rather than a number). This means that the numeric
    columns are called col2 to col5 in the plot.

    Overplotting data:

    Using the Iris flower data set from
    http://en.wikipedia.org/wiki/Iris_flower_data_set - saved as a
    csv file and then passed through the following (to make it easier
    to use with the scatterplots command/Data Model):

      % dmcopy "iris.csv[opt skip=1,sep=','][cols species=col1,
           sepal_length=col2, sepal_width=col3, petal_length=col4,
           petal_width=col5]" iris.fits

      species,sepal length,sepal width,petal length,petal width

      >>> add_window(9, 9, 'inches')
      >>> scatterplots('iris.fits[species=setosa]', color='red')
      >>> scatterplots('iris.fits[species=versicolor]', color='green',
                       overplot=True)
      >>> scatterplots('iris.fits[species=virginica]', color='blue',
                       overplot=True)
      >>> scatterlimits('petal_length', 0, 8)
      >>> scatterlimits('sepal_length', 4, 8)

    """

    if style not in ['all', 'upper', 'lower']:
        raise ValueError("style=all, upper, lower not '{}'".format(style))

    if ticks is not None:
        # If a user tries ticks=4.2 then silently truncate it
        origticks = ticks
        try:
            ticks = int(origticks)
        except ValueError:
            raise ValueError("ticks must be an integer, greater than 1: sent '{}'".format(origticks))

        if ticks < 2:
            raise ValueError("ticks must be an integer, greater than 1: sent '{}'".format(origticks))

    edata = _extract_data(data)
    _scatterplots(edata, style=style,
                  margin=margin, gap=gap, symbol=symbol,
                  color=color, size=size, fill=fill,
                  ticks=ticks, overplot=overplot)


@add_chips_undo_buffer()
def _change_scale(ids, logit):
    """Helper for scatterlog()/lin().

    When changing to a log scale the mode is changed to limits,
    but it is not restored when it is changed back since there
    is no way to know what it was (without the use of hidden
    state, which I am trying to avoid).
    """

    # TODO: restore currency
    matches = _match_axis_names(ids)
    if matches is None:
        return

    lnames = [n for (u, n) in matches]
    v3("Found the following axis names: {}".format(lnames))

    # TODO: because of bound axes we only need to do this for
    # one row/column, not all plots. however, this requires
    # parsing the plot structure to find out what the style
    # was (all/upper/lower), and then using that. For the
    # moment go with the easier approach, but add in a check
    # to only change the scale when needed, to avoid filling
    # up the undo/redo stack.
    #
    # The check for axis scale uses the isomorphism in Python
    # betwene 0/1 (from get_axis_scale) and False/True (logit)
    #
    if logit:
        scalefunc = pychips.log_scale
    else:
        scalefunc = pychips.lin_scale

    prefs = pychips.get_preferences()
    ax1 = prefs.axis.x.stem + "1"
    ay1 = prefs.axis.y.stem + "1"

    # Need to change all existing rows/columns, even if the other
    # column is not in the list, so need to iterate through anames
    # as well as lnames. Note that a lot of this is not needed because
    # of the bound axes.
    #
    anames = _get_axis_names()
    for aname in lnames:
        for aother in anames:
            # TODO: special case aname == aother

            pname1 = "plot_{}_{}".format(aname, aother)
            pname2 = "plot_{}_{}".format(aother, aname)

            # need to do in two try/except blocks so that
            # if the first fails we can try the second
            try:
                pychips.current_plot(pname1)
                # only change the mode if changing to a log scale
                if logit and pychips.get_xaxis().majortick.mode != 'limits':
                    v3("Changing Y axis majortick.mode for plot {}".format(pname1))
                    pychips.set_xaxis(['majortick.mode', 'limits'])
                if pychips.get_axis_scale(ax1) != logit:
                    v3("Changing X axis scale for plot {}".format(pname1))
                    scalefunc(pychips.X_AXIS)
            except:
                pass

            try:
                pychips.current_plot(pname2)
                # only change the mode if changing to a log scale
                if logit and pychips.get_yaxis().majortick.mode != 'limits':
                    v3("Changing Y axis majortick.mode for plot {}".format(pname2))
                    pychips.set_yaxis(['majortick.mode', 'limits'])
                if pychips.get_axis_scale(ay1) != logit:
                    v3("Changing Y axis scale for plot {}".format(pname2))
                    scalefunc(pychips.Y_AXIS)
            except:
                pass

    # TODO: restore currency


def scatterlog(ids):
    """Change the axes for the given variable names to log scale. This will
    only work on plots created by the scatterplots() command.

    Parameters
    ----------
    ids : list of variable names or numbers
        Which variables to change to a log scale. The values can be
        the variable name or an integer value (with the first column
        in the plot being 0). The list can contain both names and
        integer values. The check for names is case insensitive,
        and unrecognized columns are ignored.

    Notes
    -----

    The majortick mode is changed to limits, since that works better
    for log scale axes.

    Examples
    --------

      >>> scatterlog(['lx', 'fx'])
      >>> scatterlog([0, 3, 4])

    """

    _change_scale(ids, True)


def scatterlin(ids):
    """Change the axes for the given variable names to linear scale. This
    will only work on plots created by the scatterplots() command.

    Parameters
    ----------
    ids : list of variable names or numbers
        Which variables to change to a linear scale. The values can be
        the variable name or an integer value (with the first variable
        in the plot being 0). The list can contain both names and
        integer values. The check for names is case insensitive,
        and unrecognized variables are ignored.

    Notes
    -----

    The majortick mode is not changed by this command; so if you
    called

        scatterplots(..., ticks=2)
        scatterlog(...)
        scatterlin(...)

    then the result will not match the original scatteplots() output,
    since the scaling on the axes that were logged and then restored
    to linear scale will have changed from using 2 major tick marks to
    the "limits" mode.

    Examples
    --------

      >>> scatterlin(['lx', 'fx'])
      >>> scatterlin([0, 3, 4])

    """

    _change_scale(ids, False)


@add_chips_undo_buffer()
def scatterlimits(colid, lo, hi, mode='limits'):
    """Change the axes for the given variable name to display the range lo
    to hi, using the given majortick.mode. This will only work on
    plots created by the scatterplots() command.

    Parameters
    ----------
    colid : variable name or number
        The value can be the variable name or an integer value (with the
        first variable in the plot being 0). The check for names
        is case insensitive, and unrecognized columns are ignored.
    lo, hi : float
        Minimum and maximum value to display for the variable.
    mode: None or one of the ChIPS majortick.mode settings
        If not None then change the majortick.mode value for the axis
        to this value. The default mode used for axes created by the
        scatterplots() command is 'count'; if you want to display the
        exact range between lo and hi then 'limits' should be used (the
        default value).

    Examples
    --------

      >>> scatterlimits(lx, 1e-14, 2e-13)

    """

    matches = _match_axis_names([colid])
    if matches is None:
        return

    axnames = _get_axis_names()

    # There should only be one match, but allow for multiple.
    for (username, axname) in matches:
        v3("Changing limits of column {} / {}".format(username, axname))

        for oname in axnames:
            pname = _plot_name(axname, oname)
            try:
                pychips.current_plot(pname)
                pychips.get_xaxis()

                if mode is not None and \
                   pychips.get_xaxis().majortick.mode != mode:
                    pychips.set_xaxis(['majortick.mode', mode])

                (xlo, xhi) = pychips.get_plot_xrange()
                if xlo != lo or xhi != hi:
                    pychips.limits(pychips.X_AXIS, lo, hi)

                v3("set x axis: {} y axis: {}".format(axname, oname))
            except RuntimeError:
                v3("skipped x axis: {} y axis: {}".format(axname, oname))

            pname = _plot_name(oname, axname)
            try:
                pychips.current_plot(pname)
                pychips.get_yaxis()

                if mode is not None and \
                   pychips.get_yaxis().majortick.mode != mode:
                    pychips.set_yaxis(['majortick.mode', mode])

                (ylo, yhi) = pychips.get_plot_yrange()
                if ylo != lo or yhi != hi:
                    pychips.limits(pychips.Y_AXIS, lo, hi)

                v3("set y axis: {} x axis: {}".format(axname, oname))
            except RuntimeError:
                v3("skipped y axis: {} x axis: {}".format(axname, oname))


# Short-form variants

splots  = scatterplots
slog    = scatterlog
slin    = scatterlin
slimits = scatterlimits

# End
