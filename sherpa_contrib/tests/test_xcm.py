#
#  Copyright (C) 2021
#            Smithsonian Astrophysical Observatory
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA.
#

"""
Test routines for the convert_xspec_script code
"""

from io import StringIO
import os

import pytest

from sherpa_contrib.xspec import xcm


def check(expected, answer):
    print(answer)  # makes it easier to see on a failure
    texps = expected.split('\n')
    tanss = answer.split('\n')
    for texp, tans in zip(texps, tanss):
        assert tans == texp

    assert len(tanss) == len(texps)


def test_powerlaw():
    """model powerlaw"""

    expected = """from sherpa.astro.ui import *


# model powerlaw
m1 = create_model_component('xspowerlaw', 'm1')

# Set up the model expressions
#
set_source(1, m1)
"""

    f = StringIO('model powerlaw')
    answer = xcm.convert(f)
    check(expected, answer)


@pytest.mark.parametrize('expr',
                         ['phabs * powerlaw',
                          'phabs(powerlaw)',
                          'phabs* powerlaw'])
def test_absorbed_powerlaw(expr):
    """model powerlaw"""

    expected = f"""from sherpa.astro.ui import *


# model {expr}
m1 = create_model_component('xsphabs', 'm1')
m2 = create_model_component('xspowerlaw', 'm2')

# Set up the model expressions
#
set_source(1, m1 * m2)
"""

    f = StringIO(f'model {expr}')
    answer = xcm.convert(f)
    check(expected, answer)


@pytest.mark.parametrize('expr',
                         ['cflux(powerlaw)',
                          'cflux * powerlaw'])
def test_cflux_powerlaw(expr):
    """cflux of powerlaw"""

    expected = f"""from sherpa.astro.ui import *


# model {expr}
m1 = create_model_component('xscflux', 'm1')
m2 = create_model_component('xspowerlaw', 'm2')

# Set up the model expressions
#
set_source(1, m1(m2))
"""

    f = StringIO(f'model {expr}')
    answer = xcm.convert(f)
    check(expected, answer)


def test_cflux_absorbed_powerlaw1():
    """cflux of absorbed powerlaw

    Note the output isn't guaranteed to be the same for all the
    tests so we need separate ones.
    """

    expected = f"""from sherpa.astro.ui import *


# model cflux*(phabs * powerlaw )
m1 = create_model_component('xscflux', 'm1')
m2 = create_model_component('xsphabs', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1(m2 * m3))
"""

    f = StringIO(f'model cflux*(phabs * powerlaw )')
    answer = xcm.convert(f)
    check(expected, answer)


def test_cflux_absorbed_powerlaw2():
    """cflux of absorbed powerlaw

    Note the output isn't guaranteed to be the same for all the
    tests so we need separate ones.
    """

    expected = f"""from sherpa.astro.ui import *


# model cflux(phabs(powerlaw))
m1 = create_model_component('xscflux', 'm1')
m2 = create_model_component('xsphabs', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1(m2 * m3))
"""

    f = StringIO(f'model cflux(phabs(powerlaw))')
    answer = xcm.convert(f)
    check(expected, answer)


def test_cflux_absorbed_powerlaw3():
    """cflux of absorbed powerlaw

    I am not convinced that we have the correct interpretation
    of this as I don't find the model command documentation to
    really explain the difference between

        clux(phabs*powerlaw)
        cflux*phabs*powerlaw
    """

    expected = f"""from sherpa.astro.ui import *


# model cflux*phabs*powerlaw
m1 = create_model_component('xscflux', 'm1')
m2 = create_model_component('xsphabs', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1(m2 * m3))
"""

    f = StringIO(f'model cflux*phabs*powerlaw')
    answer = xcm.convert(f)
    check(expected, answer)


def test_absorbed_cflux_powerlaw1():
    """absorbed cflux powerlaw"""

    expected = f"""from sherpa.astro.ui import *


# model phabs * cflux(powerlaw )
m1 = create_model_component('xsphabs', 'm1')
m2 = create_model_component('xscflux', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1 * m2(m3))
"""

    f = StringIO(f'model phabs * cflux(powerlaw )')
    answer = xcm.convert(f)
    check(expected, answer)


@pytest.mark.xfail
def test_absorbed_cflux_powerlaw2():
    """absorbed cflux powerlaw"""

    expected = f"""from sherpa.astro.ui import *


# model phabs(cflux(powerlaw))
m1 = create_model_component('xsphabs', 'm1')
m2 = create_model_component('xscflux', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1 * m2(m3))
"""

    f = StringIO(f'model phabs(cflux(powerlaw)))')
    answer = xcm.convert(f)
    check(expected, answer)


@pytest.mark.xfail
def test_absorbed_cflux_powerlaw():
    """absorbed cflux powerlaw"""

    expected = f"""from sherpa.astro.ui import *


# model phabs(cflux*powerlaw)
m1 = create_model_component('xsphabs', 'm1')
m2 = create_model_component('xscflux', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')

# Set up the model expressions
#
set_source(1, m1 * m2(m3))
"""

    f = StringIO(f'model phabs(cflux*powerlaw))')
    answer = xcm.convert(f)
    check(expected, answer)


@pytest.mark.xfail
def test_atable_expression():
    """This requires the Sherpa test data to be available
    at the SHERPATESTDIR environment variable.
    """

    path = os.getenv('SHERPATESTDIR')
    if path is None:
        pytest.skip("Need SHERPATESTDIR environment variable")

    expected = f"""from sherpa.astro.ui import *


# model mtable{xspec-tablemodel-RCS.mod}(zpowerlw)
load_table_model('m1', 'xspec-tablemodel-RCS.mod')
m1 = get_model_component('m1')
m2 = create_model_component('xszpowerlw', 'm2')

# Set up the model expressions
#
set_source(1, m1 * m2)
"""

    f = StringIO('model mtable{xspec-tablemodel-RCS.mod}(zpowerlw)')

    # How to run this test and get back to the correct directory whatever
    # happens?
    thisdir = os.getcwd()
    os.chdir(path)

    try:
        answer = xcm.convert(f)
    finally:
        os.chdir(thisdir)

    check(expected, answer)


def test_param_powerlaw():
    """Check the parameter handling"""

    expected = f"""from sherpa.astro.ui import *


# model  powerlaw
m1 = create_model_component('xspowerlaw', 'm1')
set_par(m1.PhoIndex, 1.7)
set_par(m1.norm, 0.023, max=1e+20)

# Set up the model expressions
#
set_source(1, m1)
"""

    f = StringIO("""model  powerlaw
            1.7       0.01         -3         -2          9         10
          0.023       0.01          0          0      1e+20      1e+24
""")
    answer = xcm.convert(f)
    check(expected, answer)


def test_param_powerlaw_links():
    """Check the parameter handling"""

    expected = f"""from sherpa.astro.ui import *


# model  constant(powerlaw + powerlaw)
m1 = create_model_component('xsconstant', 'm1')
m2 = create_model_component('xspowerlaw', 'm2')
m3 = create_model_component('xspowerlaw', 'm3')
set_par(m1.factor, 2)
set_par(m2.PhoIndex, 1.7)
set_par(m2.norm, 3, max=1e+20)
link(m3.PhoIndex, m2.PhoIndex)
set_par(m3.norm, 4, max=1e+20)

# Set up the model expressions
#
set_source(1, m1 * (m2 + m3))
"""

    f = StringIO("""
model  constant(powerlaw + powerlaw)
              2       0.01          0          0      1e+10      1e+10
            1.7       0.01         -3         -2          9         10
              3       0.01          0          0      1e+20      1e+24
= p2
              4       0.01          0          0      1e+20      1e+24

""")
    answer = xcm.convert(f)
    check(expected, answer)
