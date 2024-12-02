"""Check ciao_contrib._tools.utils"""

import pytest

from ciao_contrib.logger_wrapper import get_verbosity, set_verbosity
from ciao_contrib._tools import utils


@pytest.fixture
def verbose0():
    orig = get_verbosity()
    set_verbosity(0)
    yield
    set_verbosity(orig)


@pytest.fixture
def verbose1():
    orig = get_verbosity()
    set_verbosity(1)
    yield
    set_verbosity(orig)


def test_list_multi_obi_obsids_is_copy():
    x = utils.list_multi_obi_obsids()
    x[0] = -43
    y = utils.list_multi_obi_obsids()
    assert y[0] == 82


def test_list_multi_obi_obsids_size():
    assert len(utils.list_multi_obi_obsids()) == 30


def test_list_multi_obi_obsids_is_ordered():
    x = utils.list_multi_obi_obsids()
    y = sorted(x)
    assert x == y


@pytest.mark.parametrize('obsid',
                         [82, 108, 279, 3764, 62249, 62264, 62796])
def test_is_multi_obi(obsid):
    """This is just a check we can copy values..."""
    assert utils.is_multi_obi_obsid(obsid)


@pytest.mark.parametrize('obsid', ['merged', 'Merged', 'MERGED'])
def test_obsid_fails_if_merged(obsid):

    with pytest.raises(ValueError) as ve:
        utils.ObsId(obsid)

    assert str(ve.value) == f"The OBS_ID value is '{obsid}'"


def test_obsid_basic():
    o = utils.ObsId('1024')
    assert o.obsid == '1024'
    assert o.cycle is None
    assert o.obi is None
    assert not o.is_multi_obi

    assert str(o) == '1024'


@pytest.mark.parametrize('cycle', ['P', 'S'])
def test_obsid_basic_cycle(cycle):
    o = utils.ObsId('1024', cycle)
    assert o.obsid == '1024'
    assert o.cycle == cycle
    assert o.obi is None
    assert not o.is_multi_obi

    out = '1024e' + ('2' if cycle == 'S' else '1')
    assert str(o) == out


def test_obsid_basic_cycle_invalid(verbose1, caplog):

    assert len(caplog.record_tuples) == 0

    o = utils.ObsId('1024', cycle='p')

    assert len(caplog.record_tuples) == 1
    mod, lvl, msg = caplog.record_tuples[0]
    assert mod == 'cxc.ciao.contrib.module._tools.utils'
    assert lvl == 20
    assert msg == 'WARNING: ObsId 1024 has unrecognized CYCLE=p, assuming not interleaved.'

    assert o.obsid == '1024'
    assert o.cycle is None
    assert o.obi is None
    assert not o.is_multi_obi

    assert str(o) == '1024'


@pytest.mark.parametrize('obi', ['000', '001'])
def test_obsid_basic_obi(obi):
    """By default the OBI is ignored"""
    o = utils.ObsId('1024', obi=obi)
    assert o.obsid == '1024'
    assert o.cycle is None
    assert o.obi == int(obi)
    assert not o.is_multi_obi

    assert str(o) == '1024'


def test_obsid_basic_obi_not_multi():

    o = utils.ObsId('1024', obi='002')
    with pytest.raises(ValueError) as ve:
        o.is_multi_obi = True

    assert str(ve.value) == 'ObsId 1024 is not recognized as a multi-OBI dataset.'


def test_obsid_basic_obi_invalid_negative(verbose1, caplog):

    assert len(caplog.record_tuples) == 0

    o = utils.ObsId('1024', obi='-2')

    assert len(caplog.record_tuples) == 1
    mod, lvl, msg = caplog.record_tuples[0]
    assert mod == 'cxc.ciao.contrib.module._tools.utils'
    assert lvl == 20
    assert msg == 'WARNING: ObsId 1024 has obi=-2 which is < 0; ignoring.'

    assert o.obsid == '1024'
    assert o.cycle is None
    assert o.obi is None
    assert not o.is_multi_obi

    assert str(o) == '1024'


def test_obsid_basic_obi_invalid_not_a_number(verbose1, caplog):

    assert len(caplog.record_tuples) == 0

    o = utils.ObsId('1024', obi='x')

    assert len(caplog.record_tuples) == 1
    mod, lvl, msg = caplog.record_tuples[0]
    assert mod == 'cxc.ciao.contrib.module._tools.utils'
    assert lvl == 20
    assert msg == 'WARNING: ObsId 1024 has invalid obi=x (expected integer); ignoring.'

    assert o.obsid == '1024'
    assert o.cycle is None
    assert o.obi is None
    assert not o.is_multi_obi

    assert str(o) == '1024'


def test_obsid_multi_obi_no_obi():
    """Pick a known multi-obi case"""

    with pytest.raises(utils.MultiObiError) as me:
        utils.ObsId('3057')

    assert str(me.value) == 'For multi-OBI datasets like 3057 the obi argument must be set'


def test_obsid_multi_obi():
    """Pick a known multi-obi case"""

    o = utils.ObsId('3057', obi='002')
    assert o.obsid == '3057'
    assert o.cycle is None
    assert o.obi == 2
    assert o.is_multi_obi

    assert str(o) == '3057_002'


def test_print_version_v0(verbose0, caplog):

    assert len(caplog.record_tuples) == 0
    utils.print_version('bob', '0.1')
    assert len(caplog.record_tuples) == 0


def test_print_version_v1(verbose1, caplog):

    assert len(caplog.record_tuples) == 0
    utils.print_version('bob', '0.1')
    assert len(caplog.record_tuples) == 2
    for mod, lvl, _ in caplog.record_tuples:
        assert mod == 'cxc.ciao.contrib.module._tools.utils'
        assert lvl == 20

    msg = caplog.record_tuples[0][2]
    assert msg == 'Running bob'

    msg = caplog.record_tuples[1][2]
    assert msg == 'Version: 0.1\n'


@pytest.mark.parametrize('outroot,outdir,outhead',
                         [('foo', '', 'foo_'),
                          ('foo/', 'foo/', ''),
                          ('foo/bar', 'foo/', 'bar_'),
                          ('', '', '')  # should this be an error?
                          ])
def test_split_outroot(outroot, outdir, outhead):
    adir, ahead = utils.split_outroot(outroot)
    assert adir == outdir
    assert ahead == outhead


@pytest.mark.parametrize('val,expected',
                         [('indef', None),
                          ('INDEF', None),
                          ('2', 2),
                          ('2.0', 2),
                          ('-1', -1),
                          ('-1.0', -1),
                          ('2.1', 2.1),
                          ('-2.1', -2.1),
                         ])
def test_to_number(val, expected):

    ans = utils.to_number(val)
    if expected is None:
        assert ans is None
        return

    assert ans == expected
    assert type(ans) == type(expected)


def test_to_number_invalid():

    with pytest.raises(ValueError) as ve:
        utils.to_number('2x')

    assert str(ve.value) == "Unable to convert '2x' to a number."


@pytest.mark.parametrize('vals,expected',
                         [([1, 3, 2], [1, 3, 2]),
                          (["1", "3", "2"], ["1", "3", "2"]),
                          ([1, 3, 3, 2, 1], [1, 3, 2]),
                          ([1, 1, 1, 1], [1]),
                          ([], [])
                         ])
def test_getUniqueSynset(vals, expected):
    out = utils.getUniqueSynset(vals)
    assert out == expected


@pytest.mark.parametrize("val", [None, "", "none", "None", "0", "0%", ":"])
def test_thresh_is_not_set(val):
    assert not utils.thresh_is_set(val)


@pytest.mark.parametrize("val", ["2", "2:", "2%"])
def test_thresh_is_set(val):
    assert utils.thresh_is_set(val)


@pytest.mark.parametrize("invalid,msg",
                         [("" ,"Expected a:b:c or a:b:#c, not "),
                          ("2", "Expected a:b:c or a:b:#c, not 2"),
                          ("2:3", "Expected a:b:c or a:b:#c, not 2:3"),
                          ("2:3:0.2:2", "Expected a:b:c or a:b:#c, not 2:3:0.2:2"),

                          # errors for lo/hi
                          ("::", "Unable to convert '' to a number."),
                          ("x::", "Unable to convert 'x' to a number."),
                          ("2::", "Unable to convert '' to a number."),
                          ("2:x:", "Unable to convert 'x' to a number."),

                          ("2:3:#x", "Unable to convert 'x' to a number."),
                          ("2:3:#0", "Number of bins must be > 0 in 2:3:#0"),
                          ("2:3:#-1", "Number of bins must be > 0 in 2:3:#-1"),
                          ("2:3:0", "The binsize must be > 0 in 2:3:0"),
                          ("2:3:-0.2", "The binsize must be > 0 in 2:3:-0.2"),
                          ])
def test_parse_range_errors(invalid, msg):
    """TODO: we should error out when lo >= hi"""

    with pytest.raises(ValueError) as ve:
        utils.parse_range(invalid)

    assert str(ve.value) == msg


def test_parse_range_nbins():

    lo, hi, binsize, nbins = utils.parse_range('2:12:#10')
    assert lo == 2.0
    assert hi == 12.0
    assert binsize == 1.0
    assert nbins == 10


def test_parse_range_stepsize():

    lo, hi, binsize, nbins = utils.parse_range('2:12:1')
    assert lo == 2.0
    assert hi == 12.0
    assert binsize == 1.0
    assert nbins == 10


@pytest.mark.parametrize("invalid,msg",
                         [("", "xygrid should be a filename or 2 ranges separated by a comma, not ''!"),
                          ("2:12:1", "xygrid should be a filename or 2 ranges separated by a comma, not '2:12:1'!"),
                          ("foo,bar", "xygrid should be a filename or xlo:xhi:#nx or dx,ylo:yhi:#ny or dy, not 'foo,bar'!"),

                          ])
def test_parse_xygrid_string_errors(invalid, msg):
    """This is slightly tricky as invalid must not match an image file name"""

    with pytest.raises(ValueError) as ve:
        utils.parse_xygrid(invalid)

    assert str(ve.value) == msg


def test_parse_xygrid_string_square():

    outstr, binsize, xrng, yrng, nbins = utils.parse_xygrid('2:12:1, 3:12:1')
    assert outstr == 'x=2:12:1,y= 3:12:1'
    assert binsize == 1
    assert xrng == (2, 12)
    assert yrng == (3, 12)
    assert nbins == (10, 9)


def test_parse_xygrid_string_rectangle():

    outstr, binsize, xrng, yrng, nbins = utils.parse_xygrid('2:12:#10,3:12:#18')
    assert outstr == 'x=2:12:#10,y=3:12:#18'
    assert binsize == 0.5
    assert xrng == (2, 12)
    assert yrng == (3, 12)
    assert nbins == (10, 18)


@pytest.mark.parametrize("invalid", ["12", "foobar", "12 , 13,14", ",23", " ,  23  "])
def test_parse_refpos_string_errors(invalid):
    with pytest.raises(ValueError) as ve:
        utils.parse_refpos(invalid)

    assert str(ve.value) == f'Unable to parse {invalid} as a ra and dec value.'


@pytest.mark.parametrize("invalid", ["x,23", "12:23:45:2,23"])
def test_parse_refpos_string_errors_ra(invalid):
    with pytest.raises(ValueError) as ve:
        utils.parse_refpos(invalid)

    assert str(ve.value).startswith(f'Could not parse the RA value, ')


@pytest.mark.parametrize("invalid", ["23,x", "12:23:45.2,12:23:45:23", "12,-100", "12, 100"])
def test_parse_refpos_string_errors_dec(invalid):
    with pytest.raises(ValueError) as ve:
        utils.parse_refpos(invalid)

    assert str(ve.value).startswith(f'Could not parse the Dec value, ')


@pytest.mark.parametrize("arg", [""," ", "           "])
def test_parse_refpos_empty_string(arg):
    assert utils.parse_refpos(arg) is None


def test_parse_refpos():
    ra, dec, dummy = utils.parse_refpos(" 12 , -0.1 ")
    assert dummy is None
    assert ra == 12.0
    assert dec == -0.1


def test_sky_to_arcsec_invalid():
    with pytest.raises(ValueError) as ve:
        utils.sky_to_arcsec('XMM', 23)

    assert str(ve.value) == "Invalid instrume=XMM argument, expected ACIS or HRC."


def test_sky_to_arcsec_acis():
    out = utils.sky_to_arcsec('ACIS', 1000)
    assert out == 492.0


def test_sky_to_arcsec_hrc():
    out = utils.sky_to_arcsec('HRC', 10000)
    assert out == 1318.0
