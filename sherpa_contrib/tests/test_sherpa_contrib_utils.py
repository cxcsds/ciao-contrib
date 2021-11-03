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
Test sherpa_contrib.utils
"""

import logging

import numpy as np

import pytest

from sherpa.astro import instrument
from sherpa.astro import ui
from sherpa.utils.err import ArgumentErr, ParameterErr

from sherpa_contrib.utils import renorm


@pytest.fixture
def reset():
    """Run the test with a clean environment"""
    ui.clean()
    yield
    ui.clean()


@pytest.fixture
def setup_src():
    """Create a basic source"""

    chans = np.arange(1, 11, dtype=np.int16)
    counts = np.asarray([1, 2, 3, 3, 2, 1, 0, 1, 2, 0], dtype=np.int16)
    ui.load_arrays(1, chans, counts, ui.DataPHA)

    # fake up a response
    egrid = np.arange(1, 12) * 0.1
    elo = egrid[:-1]
    ehi = egrid[1:]
    arf = instrument.create_arf(elo, ehi)
    ui.set_arf(arf)


def test_renorm_empty_names():
    with pytest.raises(ArgumentErr) as ae:
        renorm(names=[])

    assert str(ae.value) == "Invalid names argument: '[]'"


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_no_thawed_norm(model, reset, setup_src, caplog):
    """WHat happens if the parameter is frozen?"""

    mdl = ui.create_model_component(model, 'mdl')
    ui.set_source(mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    mdl.pars[-1].frozen = True

    assert caplog.record_tuples == []

    with caplog.at_level(logging.INFO):
        renorm()

    # Check we got a warning
    assert caplog.record_tuples == [('sherpa', logging.WARN,
                                     'no thawed parameters found matching: ampl, norm')]

    # slope and normalization unchanged
    assert mdl.pars[0].val == pytest.approx(1.2)
    assert mdl.pars[-1].val == pytest.approx(1.0)


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_no_matching_name(model, reset, setup_src, caplog):
    """Let's give a silly name"""

    mdl = ui.create_model_component(model, 'mdl')
    ui.set_source(mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    mdl.pars[-1].frozen = True

    assert caplog.record_tuples == []

    with caplog.at_level(logging.INFO):
        renorm(names=['FOObar', 'bazFoo', 'bob'])

    # Check we got a warning
    assert caplog.record_tuples == [('sherpa', logging.WARN,
                                     'no thawed parameters found matching: foobar, bazfoo, bob')]

    # slope and normalization unchanged
    assert mdl.pars[0].val == pytest.approx(1.2)
    assert mdl.pars[-1].val == pytest.approx(1.0)


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_outside_range_high(model, reset, setup_src):
    """What happens if the normalization is too high.

    Actually, I'm wondering when/how we can test the ParameterErr
    check logic, as how do we trigger it?
    """

    # The idea is that the hard maximum is often 3.4e38
    # so if we scale the counts to a large-enpugh value
    # we can trigger the failure case.
    #
    y = ui.get_data().counts
    ui.set_dep(1e38 * y)

    mdl = ui.create_model_component(model, 'mdl')

    ui.set_source(mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    assert mdl.pars[-1].val == pytest.approx(1)

    with pytest.raises(ParameterErr) as pe:
        renorm()

    emsg = f'parameter mdl.{mdl.pars[-1].name} has a maximum of 3.40282e+38'
    assert str(pe.value) == emsg


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_no_data(model, reset, setup_src, caplog):
    """What happens if their is no data?"""

    y = ui.get_data().counts
    ui.set_dep(np.zeros_like(y))

    mdl = ui.create_model_component(model, 'mdl')

    ui.set_source(mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    assert mdl.pars[-1].val == pytest.approx(1)

    assert caplog.record_tuples == []

    with caplog.at_level(logging.INFO):
        renorm()

    # Check we got a warning
    assert caplog.record_tuples == [('sherpa', logging.ERROR,
                                     'data sum evaluated to <= 0; no re-scaling attempted')]

    # values don't change
    assert mdl.pars[0].val == pytest.approx(1.2)
    assert mdl.pars[-1].val == pytest.approx(1)
    assert mdl.pars[-1].min == pytest.approx(0)
    assert mdl.pars[-1].max >= 1e24


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_single_cpt(model, reset, setup_src):
    """Check we can rescale a simple component"""

    mdl = ui.create_model_component(model, 'mdl')
    ui.set_source(mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    assert mdl.pars[-1].val == pytest.approx(1)
    assert mdl.pars[-1].min == pytest.approx(0)
    # max is either 3.4e38 or 1e24
    assert mdl.pars[-1].max >= 1e24

    renorm()

    # slope unchanged
    assert mdl.pars[0].val == pytest.approx(1.2)

    # normalization changed
    val = 4.968740850227226
    assert mdl.pars[-1].val == pytest.approx(val)
    assert mdl.pars[-1].min == pytest.approx(val / 10000)
    assert mdl.pars[-1].max == pytest.approx(val * 10000)


@pytest.mark.parametrize('model', ['powlaw1d', 'xspowerlaw'])
def test_renorm_absorbed_cpt(model, reset, setup_src):
    """Check we can rescale an absorbed component"""

    # we don't care that xswabs is not for science here
    amdl = ui.create_model_component('xswabs', 'amdl')
    amdl.nh = 0.1

    mdl = ui.create_model_component(model, 'mdl')
    ui.set_source(amdl * mdl)

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2

    assert mdl.pars[-1].val == pytest.approx(1)
    assert mdl.pars[-1].min == pytest.approx(0)
    # max is either 3.4e38 or 1e24
    assert mdl.pars[-1].max >= 1e24

    renorm()

    # slope unchanged
    assert mdl.pars[0].val == pytest.approx(1.2)

    # normalization changed; thanks to the absorption it
    # is larger than the test_renorm_single_cpt case.
    #
    val = 22.1179
    assert mdl.pars[-1].val == pytest.approx(val)
    assert mdl.pars[-1].min == pytest.approx(val / 10000)
    assert mdl.pars[-1].max == pytest.approx(val * 10000)


@pytest.mark.parametrize('model,omodel',
                         [('powlaw1d', 'xspowerlaw'),
                          ('xspowerlaw', 'powlaw1d')])
def test_renorm_specify_cpt(model, omodel, reset, setup_src):
    """Check we change the requested component"""

    # we don't care that xswabs is not for science here
    amdl = ui.create_model_component('xswabs', 'amdl')
    amdl.nh = 0.1

    mdl = ui.create_model_component(model, 'mdl')
    omdl = ui.create_model_component(omodel, 'omdl')

    ui.set_source(amdl * (omdl + mdl))

    # tweak the slope (it is the first argument for both)
    mdl.pars[0].val = 1.2
    omdl.pars[0].val = 1.2

    assert mdl.pars[-1].val == pytest.approx(1)
    assert omdl.pars[-1].val == pytest.approx(1)

    renorm(cpt=amdl * mdl)

    # slope unchanged
    assert mdl.pars[0].val == pytest.approx(1.2)
    assert omdl.pars[0].val == pytest.approx(1.2)

    # check only one normalization has changed
    #
    val = 22.1179
    assert mdl.pars[-1].val == pytest.approx(val)
    assert mdl.pars[-1].min == pytest.approx(val / 10000)
    assert mdl.pars[-1].max == pytest.approx(val * 10000)

    assert omdl.pars[-1].val == pytest.approx(1)
    assert omdl.pars[-1].min == pytest.approx(0)
    assert omdl.pars[-1].max >= 1e24
