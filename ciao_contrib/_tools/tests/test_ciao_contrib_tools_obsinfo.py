"""test ciao_contrib._tools.obsinfo"""

import os
from pathlib import Path

import pytest

from ciao_contrib._tools import obsinfo


def test_normalize_path_not_absolute():
    with pytest.raises(ValueError) as ve:
        obsinfo.normalize_path('foo/bar')

    assert str(ve.value) == "Expected an absolute path for fname=foo/bar"


def test_normalize_path_in_cwd():
    cwd = os.getcwd()
    infile = f'{cwd}/foo/bar.fits'

    ans = obsinfo.normalize_path(infile)
    assert ans == 'foo/bar.fits'


def test_normalize_path_different_basedir():
    """Could create a temp directory but assume /foo is not valid"""

    infile = '/foo/foo/bar.fits'
    ans = obsinfo.normalize_path(infile)
    assert ans == infile


def test_normalize_path_same_basedir():

    # this is not really a sensible way to calculate the number of hops
    infile = Path() / '..' / '..' / 'foo' / 'bar.fits'
    infile = str(infile.resolve())

    ans = obsinfo.normalize_path(infile)

    expected = '../../foo/bar.fits'
    assert ans == expected


def test_obsinfo_not_a_file():
    with pytest.raises(OSError) as oe:
        obsinfo.ObsInfo('not-a-file')

    # error message is not nice!
    assert str(oe.value) == "Unable to open infile='not-a-file'\n  dmImageOpen() file does not exist. 'not-a-file'"
