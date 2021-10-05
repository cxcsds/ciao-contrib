"""Basic tests of the logger_wrapper interface"""

import logging

import pytest

from ciao_contrib import logger_wrapper as lw


NAME = 'testing'
lw.initialize_logger(NAME)


@pytest.fixture
def reset():
    yield
    lw.set_verbosity(0)


def test_default_verbosity():
    assert lw.get_verbosity() == 0


def test_default_level():
    lgr = lw.get_logger(NAME)
    assert lgr.level == 0


@pytest.mark.parametrize("v", [5, 4, 3, 2, 1])
def test_set_verbosity(v, reset):
    lw.set_verbosity(v)
    assert lw.get_verbosity() == v


@pytest.mark.parametrize("v", [0, 1, 2, 3, 4, 5])
def test_v0_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v0: v={v}"

    v0 = lw.make_verbose_level(NAME, 0)
    v0(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(0)
    assert msg == wmsg


@pytest.mark.parametrize("v", [0])
def test_v1_no_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v1: v={v}"

    v1 = lw.make_verbose_level(NAME, 1)
    v1(wmsg)

    assert len(caplog.records) == 0


@pytest.mark.parametrize("v", [1, 2, 3, 4, 5])
def test_v1_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v1: v={v}"

    v1 = lw.make_verbose_level(NAME, 1)
    v1(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(1)
    assert msg == wmsg


@pytest.mark.parametrize("v", [0, 1])
def test_v2_no_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v2: v={v}"

    v2 = lw.make_verbose_level(NAME, 2)
    v2(wmsg)

    assert len(caplog.records) == 0


@pytest.mark.parametrize("v", [2, 3, 4, 5])
def test_v2_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v2: v={v}"

    v2 = lw.make_verbose_level(NAME, 2)
    v2(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(2)
    assert msg == wmsg


@pytest.mark.parametrize("v", [0, 1, 2])
def test_v3_no_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v3: v={v}"

    v3 = lw.make_verbose_level(NAME, 3)
    v3(wmsg)

    assert len(caplog.records) == 0


@pytest.mark.parametrize("v", [3, 4, 5])
def test_v3_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v3: v={v}"

    v3 = lw.make_verbose_level(NAME, 3)
    v3(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(3)
    assert msg == wmsg


@pytest.mark.parametrize("v", [0, 1, 2, 3])
def test_v4_no_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v4: v={v}"

    v4 = lw.make_verbose_level(NAME, 4)
    v4(wmsg)

    assert len(caplog.records) == 0


@pytest.mark.parametrize("v", [4, 5])
def test_v4_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v3: v={v}"

    v4 = lw.make_verbose_level(NAME, 4)
    v4(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(4)
    assert msg == wmsg


@pytest.mark.parametrize("v", [0, 1, 2, 3, 4])
def test_v5_no_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v5: v={v}"

    v5 = lw.make_verbose_level(NAME, 5)
    v5(wmsg)

    assert len(caplog.records) == 0


@pytest.mark.parametrize("v", [5])
def test_v5_call(v, caplog, reset):
    lw.set_verbosity(v)

    wmsg = f"my message v5: v={v}"

    v5 = lw.make_verbose_level(NAME, 5)
    v5(wmsg)

    assert len(caplog.records) == 1
    lname, lvl, msg = caplog.record_tuples[0]
    assert lname == 'cxc.ciao.contrib.testing'
    assert lvl == lw._v_to_lvl(5)
    assert msg == wmsg
