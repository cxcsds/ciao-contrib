#
#  Copyright (C) 2025
#  Smithsonian Astrophysical Observatory
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

"""Calculate the Kaastra 2017 approximation for CSTAT.

This module implements an approxmate goodness-of-fit for the CSTAT
statistic using the results of `Kaastra 2017 (A&A 605, A51)
<https://ui.adsabs.harvard.edu/abs/2017A%26A...605A..51K/abstract>`_.

The three main routines are:

- `calc_cstat_gof_kaastra17`, which calculates the expected mean and
  variance for the CStat statistic for the given model,
- `show_cscat_gof_kaastra17`, which takes the results from
  `calc_cstat_gof_kaastra17` and presents them in a "nice" form,
  along with the current statistic value
- and `simulate_stats` which will simulate a dataset using the current
  model - assuming Poisson statistics - and calculate the CStat value.

The idea is that Sherpa is set up to fit data, using the "cstat"
statistic, and then a user can use `calc_cstat_gof_kaastra17` to see
what the expected statistic (and its variance) is. The
`show_cstat_gof_kaastra17` routine displays the information in the
same way that routines like `show_stat` and `show_fit` do.

The `simulate_stats` routine will use the current model to simulate
datasets and calculate the statistic value. The results can be
compared to `calc_cstat_gof_kaastra17` to see how well the Kaastra
2017 approximation does for this dataset.

"""

from collections.abc import Callable
from dataclasses import dataclass
import logging

import numpy as np
import numpy.typing as npt

from sherpa.astro import ui
from sherpa.data import Data, Data1D
from sherpa.fit import Fit
from sherpa.models.model import ArithmeticConstantModel, Model
from sherpa.stats import Stat, CStat
from sherpa.utils import sao_fcmp, send_to_pager
from sherpa.utils.random import RandomType, poisson_noise
from sherpa.utils.types import IdType

__all__ = ("calc_cstat_gof_kaastra17",
           "show_cstat_gof_kaastra17",
           "simulate_stats")


# Use the sherpa logging instance.
lgr = logging.getLogger("sherpa")


def get_fake_info(data: Data,
                  model: Model
                  ) -> tuple[Data1D, ArithmeticConstantModel]:
    """Create the data and models to use to simulate the data.

    Parameters
    ----------
    data, model
       The dataset and model to simulate

    Returns
    -------
    faked_data, faked_model
       The basic data and model used for the simulations.

    """

    actual_data, _, _ = data.to_fit()
    actual_model = data.eval_model_to_fit(model)

    fake_x = np.arange(len(actual_data))
    fake_data = Data1D("faked_data", fake_x, actual_data)
    fake_model = ArithmeticConstantModel(name="faked_model",
                                         val=actual_model)
    return fake_data, fake_model


def simulate_model_stats(data: Data,
                         model: Model,
                         stat: Stat,
                         niter: int,
                         method: Callable | None = None,
                         rng: RandomType | None = None
                         ) -> np.ndarray:
    """Simulate the data from the model and evaluate the statistic.

    Use the current model to simulate data - using the method call -
    and then evaluate the statistic. Repeat niter times and return
    the statistic values.

    Parameters
    ----------
    data
       The data.
    model
       The model fit to the data.
    stat
       The statistic object.
    niter
       The number of iteratations.
    method
       If None, the default, then the data is simulated using the
       `sherpa.utils.random.poisson_noise` routine. If set, it must be
       a callable that takes a ndarray of the predicted values and an
       optional rng argument that takes a NumPy random generator, and
       returns a ndarray of the same size with the simulated data.
    rng
       The RNG (or None) to send to method.

    Returns
    -------
    stats
       An array with niter statistic values.

    Notes
    -----

    This is only going to work reliably with Cash or CStat
    statistics. The Chi-Square statistics require an error array and
    it's unclear how best to calculate this. The WStat statistic
    is unlikley to work, thanks to the background handling, but
    it has not been tested.

    Should the data be re-grouped? This has large consequences for how
    the code is called but also the interpretation of the results.

    """

    if niter < 1:
        raise ValueError("niter must be >= 1")

    predictor = poisson_noise if method is None else method

    fake_data, fake_model = get_fake_info(data, model)

    out = np.full(niter, np.nan)
    for idx in range(niter):
        # Simulate the data based on the model prediction
        fake_data.y = predictor(fake_model.val, rng=rng)
        out[idx] = stat.calc_stat(fake_data, fake_model)[0]

    return out


def validate_model_stats(f: Fit,
                         prefix: str) -> None:
    """Check we can match the expected statistic.

    Parameters
    ----------
    f
       The fit object
    prefix
       The prefix for the warning message that is displayed if
       there is a mis-match.

    """

    lgr.debug(f"Checking statistic matches for {f.stat.name}")

    # The expected statistic can be calculated from the fit object.
    #
    expected = f.calc_stat()

    fake_data, fake_model = get_fake_info(f.data, f.model)
    got = f.stat.calc_stat(fake_data, fake_model)[0]

    # For now use a fairly "relaxed" tolerance of 10^-4.
    # Do not distinguish between "too large" or "too small".
    #
    if sao_fcmp(expected, got, tol=1e-4) == 0:
        return

    msg = f"{prefix} - expected statistic {expected} but " + \
        f"calculated {got}"
    lgr.warning(msg)


def simulate_stats(id: IdType | None = None,
                   *otherids: IdType,
                   bkg_only: bool = False,
                   niter: int = 1000,
                   method: Callable | None = None
                   ) -> np.ndarray:
    """Simulate data using the current model and calculate the statistic.

    Take the current model predictions and use them to simulate
    a data set and calculate the statistic value.

    Parameters
    ----------
    id : int or str, optional
       The data set that provides the data. If not given then all data
       sets with an associated model are fit simultaneously.
    *otherids : sequence of int or str, optional
       Other data sets to use in the calculation.
    bkg_only : bool, optional
       This keyword-only argument should be set if only the background
       fits - e.g. from a call to `fit_bkg` - should be analysed.
    niter : int, optional
       The number of iterations.
    method
       If None, the default, then the data is simulated using the
       `sherpa.utils.random.poisson_noise` routine. If set, it must be
       a callable that takes a ndarray of the predicted values and an
       optional rng argument that takes a NumPy random generator, and
       returns a ndarray of the same size with the simulated data.

    Returns
    -------
    stats
       An array of the predicted statistic value.

    Notes
    -----

    The model evaluation is over the noticed bins only, and applies
    the selected grouping column (if applicable). This means that the
    simulation will be done on the grouped channel, and not on the
    individual channels and then combined.

    This will not work with the WStat statistic.

    """

    # What identifiers should be used? This uses internals of the
    # Sherpa UI API.
    #
    session = ui._session

    if bkg_only:
        getfit = session._get_bkg_fit
    else:
        getfit = session._get_fit

    # Should this run within SherpaVerbosity("ERROR")? This will avoid
    # the user seeing warnings (e.g. background is being ignored) but
    # there is a strong argument to say they should see these warnings
    # here.
    #
    allids, f = getfit(id, otherids, numcores=1)

    # Let the user know what identifiers are in use.  Use allids in
    # case it has more entries in then id+otherids (e.g. if id is
    # None).
    #
    if len(allids) == 1:
        names = allids[0]
        msg = f"Using fit results from dataset: {names}"
        prefix = f"Dataset: {names}"
    else:
        names = str(allids).strip("[]()")
        msg = f"Using fit results from datasets: {names}"
        prefix = f"Datasets: {names}"

    lgr.info(msg)

    # Let the user know if there's a problem calculating the
    # statistic, as the current approach may break in certain
    # situations (e.g. maybe WStat).
    #
    validate_model_stats(f, prefix)

    rng = session.get_rng()
    return simulate_model_stats(f.data, f.model, f.stat,
                                niter=niter, method=method, rng=rng)

def process_range(mu: np.ndarray,
                  out: np.ndarray,
                  func: Callable[[np.ndarray], np.ndarray],
                  lo: float,
                  hi: float | None
                  ) -> None:
    """Select those mu values within [lo, hi) and fill the out values.

    Parameters
    ----------
    mu
       The model prediction values, in counts. 1D.
    out
       The array to be filled in by func. It must match mu in shape.
    func
       Given the subset of mu that matches [lo, hi), calculate the
       expected values and return them.
    lo
       The minimum value; this is "lo < mu" unless
       lo is 0, when it's "lo <= mu". lo is >= 0.
    hi
       The maximum value, if set. This is always "mu <= hi".
       hi is > lo when not None.

    """

    if lo == 0.0:
        idx = mu >= 0
    else:
        idx = mu > lo

    if hi is not None:
        idx &= (mu <= hi)

    # No items selected
    if not idx.any():
        return

    # Calculate and store the values.
    out[idx] = func(mu[idx])


def estimate_mean(mu: npt.ArrayLike) -> np.ndarray:
    """Use equations 8-12 of Kaastra 2017 to estimate cstat.

    Parameters
    ----------
    mu
       The expected (model) prediction, in counts.

    Returns
    -------
       The expected Cstat value (an approximation).

    """

    muvals = np.array(mu)

    def v1(m1):
        return -0.25 * m1**3 + 1.38 * m1**2 - 2 * m1 * np.log(m1)

    def v2(m2):
        return -0.00335 * m2**5 + 0.04259 * m2**4 \
            - 0.27331 * m2**3 + 1.381 * m2**2 - 2 * m2 * np.log(m2)

    def v3(m3):
        return 1.019275 + 0.1345 * m3**(0.461 - 0.9 * np.log(m3))

    def v4(m4):
        return 1.00624 + 0.604 / m4**1.68

    def v5(m5):
        return 1 + 0.1649 / m5 + 0.226 / m5**2

    # Model values < 0 are just set to NaN for now.
    out = np.full(muvals.shape, np.nan)

    process_range(muvals, out, v1, 0, 0.5)
    process_range(muvals, out, v2, 0.5, 2)
    process_range(muvals, out, v3, 2, 5)
    process_range(muvals, out, v4, 5, 10)
    process_range(muvals, out, v5, 10, None)
    return out


kfact = {0: 1, 1: 1, 2: 2, 3: 6, 4: 24}


def pk(k: int, mu: np.ndarray) -> np.ndarray:
    """P_k(mu) = exp(-mu) my^k / k!

    This requires k=0, 1, 2, 3, or 4.
    """

    return np.exp(-mu) * mu**k / kfact[k]


def estimate_variance(mu: npt.ArrayLike) -> np.ndarray:
    """Use equations 13-22 of Kaastra 2017 to estimate cstat variance.

    Parameters
    ----------
    mu
       The expected (model) prediction, in counts.

    Returns
    -------
       The expected variance of the Cstat value (an approximation).

    """

    muvals = np.array(mu)

    # Model values < 0 are just set to NaN for now.
    out = np.full(muvals.shape, np.nan)

    def v1(m1):
        sv = pk(0, m1) * m1**2
        for k in range(1, 5):
            sv += pk(k, m1) * (m1 - k + k * np.log(k / m1))**2

        sv *= 4

        # Convert from Sv to Cv using Cv = Sv - Ce^2
        return sv - estimate_mean(m1)**2

    def v2(m2):
        return -262 * m2**4 + 195 * m2**3 - 51.24 * m2**2 + \
            4.34 * m2 + 0.77005

    def v3(m3):
        return 4.23 * m3**2 - 2.8254 * m3 + 1.12522

    def v4(m4):
        return -3.7 * m4**3 + 7.328 * m4**2 - 3.6926 * m4 + 1.20641

    def v5(m5):
        return 1.28 * m5**4 - 5.191 * m5**3 + 7.666 * m5**2 - \
            3.5446 * m5 + 1.15431

    def v6(m6):
        return 0.1125 * m6**4 - 0.641 * m6**3 + 0.859 * m6**2 + \
            1.0914 * m6 - 0.05748

    def v7(m7):
        return 0.089 * m7**3 - 0.872 * m7**2 + 2.8422 * m7 - 0.67539

    def v8(m8):
        return 2.12336 + 0.012202 * m8**(5.717 - 2.6 * np.log(m8))

    def v9(m9):
        return 2.05159 + 0.331 * m9**(1.343 - np.log(m9))

    def v10(m10):
        return 12 / m10**3 + 0.79 / m10**2 + 0.6747 / m10 + 2

    process_range(muvals, out, v1, 0, 0.1)
    process_range(muvals, out, v2, 0.1, 0.2)
    process_range(muvals, out, v3, 0.2, 0.3)
    process_range(muvals, out, v4, 0.3, 0.5)
    process_range(muvals, out, v5, 0.5, 1)
    process_range(muvals, out, v6, 1, 2)
    process_range(muvals, out, v7, 2, 3)
    process_range(muvals, out, v8, 3, 5)
    process_range(muvals, out, v9, 5, 10)
    process_range(muvals, out, v10, 10, None)

    return out


def expected_cstat_raw(mu: np.ndarray
                       ) -> tuple[float, float]:
    """What is the Kaastra 2017 approximation for the given model?

    Parameters
    ----------
    mu
       The model values, per bin.

    Returns
    -------
    expected, variance
       The expected CStat value and its variance.

    """

    ce = estimate_mean(mu)
    cv = estimate_variance(mu)

    mean = ce.sum()
    variance = cv.sum()
    return float(mean), float(variance)


def expected_cstat(data: Data,
                   model: Model
                   ) -> tuple[float, float]:
    """Calculate the expected CStat from Kaastra 2017.

    Calculate an approxmate goodness-of-fit for the CSTAT
    statistic using the results of
    `Kaastra 2017 (A&A 605, A51)
    <https://ui.adsabs.harvard.edu/abs/2017A%26A...605A..51K/abstract>`_.

    Parameters
    ----------
    data
       The data
    model
       The model fit to the data.

    Returns
    -------
    expected, variance
       The expected CStat value and its variance.

    """

    mu = data.eval_model_to_fit(model)
    return expected_cstat_raw(mu)


@dataclass(frozen=True)
class _Kaastra17:
    """Store Kaastra 2017 information."""

    ids: list[IdType]
    fit: Fit
    mean: float
    variance: float


def _calc_cstat_gof_kaastra17(id: IdType | None = None,
                              *otherids: IdType,
                              bkg_only: bool = False
                              ) -> _Kaastra17:
    """Internal calculation of CStat using Kaastra 2017.

    Parameters
    ----------
    id : int or str, optional
       The data set that provides the data. If not given then all data
       sets with an associated model are fit simultaneously.
    *otherids : sequence of int or str, optional
       Other data sets to use in the calculation.
    bkg_only : bool, optional
       This keyword-only argument should be set if only the background
       fits - e.g. from a call to `fit_bkg` - should be analysed.

    Returns
    -------
    mapping
       The mean and variance calculated following Kaastra 2017,
       along with other useful information.

    """

    # What identifiers should be used? This uses internals of the
    # Sherpa UI API.
    #
    session = ui._session

    if bkg_only:
        func = session._get_bkg_fit
    else:
        func = session._get_fit

    ids, f = func(id, otherids, numcores=1)
    mean, var = expected_cstat(data=f.data, model=f.model)
    return _Kaastra17(ids=list(ids), fit=f, mean=mean, variance=var)


def calc_cstat_gof_kaastra17(id: IdType | None = None,
                             *otherids: IdType,
                             bkg_only: bool = False
                             ) -> tuple[float, float]:

    """Calculate the Kaastra 2017 CSTAT goodness-of-fit estimate.

    Calculate an approxmate goodness-of-fit for the CSTAT
    statistic using the results of
    `Kaastra 2017 (A&A 605, A51)
    <https://ui.adsabs.harvard.edu/abs/2017A%26A...605A..51K/abstract>`_.

    Parameters
    ----------
    id : int or str, optional
       The data set that provides the data. If not given then all data
       sets with an associated model are fit simultaneously.
    *otherids : sequence of int or str, optional
       Other data sets to use in the calculation.
    bkg_only : bool, optional
       This keyword-only argument should be set if only the background
       fits - e.g. from a call to `fit_bkg` - should be analysed.

    Returns
    -------
    cstat, variance
       The model-predicted CStat and variance, as calculated by
       Kaastra 2017.

    See Also
    --------
    show_cstat_gof_kaastra17

    Notes
    -----
    This code assumes the data has already been fit.

    """

    res = _calc_cstat_gof_kaastra17(id, *otherids,
                                    bkg_only=bkg_only)

    ids = res.ids
    if len(ids) == 1:
        msg = f"Using fit results from dataset: {ids[0]}"
    else:
        names = str(ids).strip("()[]")
        msg = f"Using fit results from datasets: {names}"

    lgr.info(msg)
    return res.mean, res.variance


def show_cstat_gof_kaastra17(id: IdType | None = None,
                             *otherids: IdType,
                             bkg_only: bool = False,
                             outfile = None,
                             clobber: bool = False
                             ) -> None:
    """Display the Kaastra 2017 CSTAT goodness-of-fit estimate.

    Calculate an approxmate goodness-of-fit for the CSTAT
    statistic using the results of
    `Kaastra 2017 (A&A 605, A51)
    <https://ui.adsabs.harvard.edu/abs/2017A%26A...605A..51K/abstract>`_.

    Parameters
    ----------
    id : int or str, optional
       The data set that provides the data. If not given then all data
       sets with an associated model are fit simultaneously.
    *otherids : sequence of int or str, optional
       Other data sets to use in the calculation.
    bkg_only : bool, optional
       This keyword-only argument should be set if only the background
       fits - e.g. from a call to `fit_bkg` - should be analysed.
    outfile : str, optional
       If not given the results are displayed to the screen, otherwise
       it is taken to be the name of the file to write the results to.
    clobber : bool, optional
       If `outfile` is not ``None``, then this flag controls whether
       an existing file can be overwritten (``True``) or if it raises
       an exception (``False``, the default setting).

    See Also
    --------
    calc_cstat_gof_kaastra17

    Notes
    -----
    This code assumes the data has already been fit.

    """

    res = _calc_cstat_gof_kaastra17(id, *otherids,
                                    bkg_only=bkg_only)

    out = []
    def msg(left, right):
        out.append(f"{left:20s} = {right}")

    ids = res.ids
    if len(ids) == 1:
        msg("Dataset", ids[0])
    else:
        idstr = str(ids).strip("()[]")
        msg("Datasets", idstr)

    msg("Statistic", res.fit.stat.name)

    c = res.fit.calc_stat()
    msg("  calculated", c)

    se = np.sqrt(res.variance)
    msg("  model prediction", f"{res.mean} +/- {se}")

    # The Kaastra approximations have relative errors of order 1e-4,
    # so restrict the number-of-sigma calculation to 4dp as we expect
    # separation values ~ 1.
    #
    diff = (c - res.mean) / se
    msg("  separation", f"{diff:.4g} sigma")

    txt = "\n".join(out)
    send_to_pager(txt, filename=outfile, clobber=clobber)

    if isinstance(res.fit.stat, CStat):
        return

    # Should this error out instead?
    lgr.warning(f"Expected CStat-based statistic, not {res.fit.stat.name}")
