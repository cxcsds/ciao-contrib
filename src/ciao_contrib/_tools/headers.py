#
#  Copyright (C) 2018, 2019
#    Smithsonian Astrophysical Observatory
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
Header routines, currently limited to merging keywords.

The idea is to move this from being text-based to being created with
methods, and having output to text for tools that need it.
"""

import math

import ciao_contrib.logger_wrapper as lw

__all__ = ("HeaderMerge", )

lgr = lw.initialize_module_logger('_tools.merging')
v2 = lgr.verbose2
v3 = lgr.verbose3
v4 = lgr.verbose4


class BaseMergeRule:
    """How should a list of keyword values be combined?

    This skips the "warn" part of the header rules.

    Parameters
    ----------
    key : str
        The name of the keyword.
    default : str or None
        The value used to replace missing keywords.

    """

    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def __str__(self):
        return "{} key={} default={}".format(self.__class__.__name__,
                                             self.key,
                                             self.default)

    def merge(self, values):
        """Merge the values.

        Parameters
        ----------
        values : sequence of values

        Returns
        -------
        value
            The new value. If None, the key should be deleted.

        """

        if len(values) == 0:
            raise ValueError("values is empty")

        if self.default is not None:
            values = [v if v is not None else self.default
                      for v in values]

        v4("Merging {}".format(values))
        newval = self._merge(values)
        v4(" -> Merged = {}".format(newval))
        return newval

    def _merge(self, values):
        """Apply the rule-specific merge.

        Parameters
        ----------
        values : sequence of values

        Returns
        -------
        value
            The new value. If None, the key should be deleted.

        """
        raise NotImplementedError()

    def _to_numeric(self, values):
        """Ensure numbers are numeric.

        Parameters
        ----------
        values : sequence
            The keyword values (possibly as strings).

        Returns
        -------
        nums : list of floats

        """

        vs = []
        for v in values:
            try:
                vs.append(float(v))
            except ValueError:
                emsg = "Keyword {} not numeric '{}'".format(self.name,
                                                            v)
                raise ValueError(emsg)

        return vs


class UseFirstMergeRule(BaseMergeRule):
    """Use the first value (even if None).

    This logic is used by a number of rules, so it has been abstracted
    out.
    """

    def _merge(self, values):
        return values[0]


class NotImplementedMergeRule(UseFirstMergeRule):
    """This rule is not properly implemented, so delete the keyword.
    """

    def _merge(self, values):
        return None


class MaxMergeRule(BaseMergeRule):
    """Return the max value"""

    def _merge(self, values):
        return max(self._to_numeric(values))


class MinMergeRule(BaseMergeRule):
    """Return the min value"""

    def _merge(self, values):
        return min(self._to_numeric(values))


class FailMergeRule(BaseMergeRule):
    """Only retain if the value is the same in all files.

    There is no warning if the keyword is missing.

    """

    def _merge(self, values):
        vs = set(values)
        return values[0] if len(vs) == 1 else None


class CalcForceMergeRule(NotImplementedMergeRule):
    """Approximate the calcForce rule.

    This does not appear to match the DataModel (e.g. using min/max
    for TSTART/TSTOP) exactly, at least according to 'ahelp
    merging_rules'.

    """

    _func = None

    def __init__(self, key, default=None):

        if key == 'TSTART':
            self._func = min
        elif key == 'TSTOP':
            self._func = max
        elif key == 'DTCOR':
            # Use the first value
            self._func = lambda xs: xs[0]

        elif key in ['DATE-OBS', 'DATE-END', 'DATE']:
            # since DATE-OBS/END are based on TSTART/TSTOP and we can't easily
            # guarantee a match up with the values written out for thise
            # keywords, it is safest to remove these.
            #
            # For DATE it is easiest to remove rather than converting
            # to a time value so they can be ordered.
            #
            self._func = lambda xs: None

        else:
            raise ValueError("Unsupported keyword {} for calcForce".format(key))

        super().__init__(key, default=default)

    def _merge(self, values):
        return self._func(values)


class CalcGTIMergeRule(BaseMergeRule):
    """Approximate the calcGTI rule.

    This just sums the input values, assuming that they do not
    overlap in time. This should be okay for the "merging observation"
    workload, but is not correct in all cases.

    It is expected that the default is set to 0, so that missing
    values are essentially skipped.
    """

    def __init__(self, key, default=None):
        # List taken from ahelp merging_rules
        for head in ['ONTIME', 'LIVETIME', 'LIVTIME', 'EXPOSUR']:
            if key.startswith(head):
                super().__init__(key, default=default)
                return

        raise ValueError("Unsupported keyword {} for calcGTI".format(key))

    def _merge(self, values):
        return sum(values)


class ForceMergeRule(UseFirstMergeRule):
    """Use the first value.

    This is not guaranteed to match the Data Model behavior,
    since

       a) the default value for a missing keyword is unclear
       b) there is no warning information.

    Note that if the first key is missing then (unless a default
    is specified) it will be set to None, so the keyword will be
    deleted.
    """

    pass


class WarnFirstMergeRule(UseFirstMergeRule):
    """Use the first value.

    Note that WarnFirst;Force-xxx is WarnFirst with the default
    value set to the given value.
    """

    pass


class WarnOmitMergeRule(BaseMergeRule):
    """Use the first value if all values are within a tolerance.

    Parameters
    ----------
    key : str
        The name of the keyword.
    tol : float
        The absolute tolerance (must be > 0).
    default : str or None
        The value used to replace missing keywords.
    """

    def __init__(self, key, tol, default=None):
        if tol <= 0.0:
            raise ValueError("tolerance must be > 0")

        self.tol = tol
        super().__init__(key, default=default)

    def __str__(self):
        return "{} key={} tol={} default={}".format(self.__class__.__name__,
                                                    self.key,
                                                    self.tol,
                                                    self.default)

    def _merge(self, values):
        if values[0] is None:
            return None

        try:
            vs = self._to_numeric(values)
        except ValueError:
            return None

        v0 = vs[0]
        for v in vs[1:]:
            if math.fabs(v - v0) > self.tol:
                return None

        return v0


class WarnPreferMergeRule(BaseMergeRule):
    """Use the default value if the keywords do not agree.

    Note that requires that the preferred value be used for the
    default value. The way the rule is written appears complicated,
    but I think the implementation is simple.
    """

    def _merge(self, values):
        if self.default is None:
            raise ValueError("default can not be None")

        vs = set(values)
        return values[0] if len(vs) == 1 else self.default


class MergeForceMergeRule(BaseMergeRule):
    """Use the force value if the keys do not agree.

    Note that requires that the "value2" value be used for the
    default value and the force value is "value1".

    Parameters
    ----------
    key : str
        The name of the keyword.
    force : value
        The value to use if the keys do not agree (value1)
    default : str
        The value used to replace missing keywords (value2)
    """

    def __init__(self, key, force, default):
        if None in [force, default]:
            raise ValueError("force and default can not be None")

        self.force = force
        super().__init__(key, default=default)

    def __str__(self):
        return "{} key={} force={} default={}".format(self.__class__.__name__,
                                                      self.key,
                                                      self.force,
                                                      self.default)

    def _merge(self, values):
        vs = set(values)
        return values[0] if len(vs) == 1 else self.force


class SkipMergeRule(BaseMergeRule):
    """Delete this key."""

    def _merge(self, values):
        return None


# Should we not bother with type-sepcific rules?
#
class PutStringMergeRule(BaseMergeRule):
    """Replace the value with the default value.

    Should this error out if the default value is not a string?
    """

    def _merge(self, values):
        if self.default is None:
            raise ValueError("default has not been set")

        return self.default


def get_value_from_rule(rulespec):
    """Does the rule specify a value?

    Parameters
    ----------
    rulespec : str
        The rule (does not include any ; character).

    Returns
    -------
    token, value : str, str or None
        The token in the rulespec and the value (None if none given)

    Examples
    --------

    >>> get_value_from_rule('MAX')
    ('Max', None)

    >>> get_value_from_rule('FORCE-ACIS')
    ('FORCE', 'ACIS')

    >>> get_value_from_rule('WarnOmit-0.01')
    ('WarnOmit', '0.01')

    """

    idx = rulespec.find('-')
    if idx == -1:
        return rulespec, None
    else:
        return rulespec[:idx], rulespec[idx + 1:]


def parse_merge_rule(key, rulespec):
    """Return the merging rule given the specification.

    Parameters
    ----------
    key : str
        The keyword to apply this to.
    rulespec : str
        The specification of the merging rule. This is the second column
        in the lookup/merging table described in ahelp merging_rules.

    Returns
    -------
    rule : a BaseMergeRule subclass

    Notes
    -----
    This does not support all the functionality of the Data Model merging
    rules. In particular stacking rules using "rule1;rule2" beyond that
    directly given in the ahelp file.

    It also does not complain if extra tokens are given, so

        MAX;Default-23

    is not flagged as an error. Should we apply the default in this case?

    """

    # A big old look-up table.
    #
    toks = rulespec.split(';')
    ntoks = len(toks)
    if ntoks > 2:
        raise ValueError("Unsupported rule for {}: {}".format(key, rulespec))

    tok1, val1 = get_value_from_rule(toks[0])
    if ntoks == 2:
        tok2, val2 = get_value_from_rule(toks[1])
        tok2 = tok2.upper()
    else:
        tok2 = ''
        val2 = None

    rupper = tok1.upper()

    if rupper == 'MAX':
        return MaxMergeRule(key)
    elif rupper == 'MIN':
        return MinMergeRule(key)
    elif rupper == 'FAIL':
        if ntoks == 2 and tok2 != 'DEFAULT':
            raise ValueError("Expected FAIL;Default-xxx but found {}".format(rulespec))

        return FailMergeRule(key, default=val2)
    elif rupper == 'CALCFORCE':
        return CalcForceMergeRule(key)
    elif rupper == 'CALCGTI':
        return CalcGTIMergeRule(key, default=0)
    elif rupper == 'FORCE':
        return ForceMergeRule(key, default=val1)
    elif rupper == 'WARNFIRST':
        if ntoks == 2 and tok2 != 'FORCE':
            raise ValueError("Expected WarnFirst;Force-xxx but found {}".format(rulespec))

        return WarnFirstMergeRule(key, default=val2)

    elif rupper == 'WARNOMIT':
        if val1 is None:
            raise ValueError("Invalid rule for WarnOmit-xxx: {}".format(rulespec))

        try:
            tol = float(val1)
        except ValueError:
            raise ValueError("WarnOmit must specify a number, sent {}".format(rulespec))

        return WarnOmitMergeRule(key, tol=tol)

    elif rupper == 'WARNPREFER':
        if val1 is None:
            raise ValueError("Invalid rule for WarnPrefer-xxx: {}".format(rulespec))

        return WarnPreferMergeRule(key, default=val1)

    elif rupper == 'MERGE':
        if tok2 != 'FORCE' or val1 is None or val2 is None:
            raise ValueError("Expected Merge-xxx;Force-yyy not {}".format(rulespec))

        return MergeForceMergeRule(key, default=val2, force=val1)

    elif rupper == 'SKIP':
        return SkipMergeRule(key)

    elif rupper == 'PUT_STRING':
        if val1 is None:
            raise ValueError("Expected PUT_STRING-xxx not {}".format(rulespec))

        return PutStringMergeRule(key, default=val1)

    raise ValueError("Invalid or unsupported merging spec for {}: {}".format(key, rulespec))


class HeaderMerge:
    """Emulate the CIAO Data Model's merging rules for header keywords.

    This does not handle the case of adding a keyword when none exist,
    since at present we have to have a key to call the apply method.
    This could be added.

    Parameters
    ----------
    lookupTable : str
        The name of the file containing the merging rules, following the
        format described by 'ahelp merging_rules'.

    """

    def __init__(self, lookupTable):
        self._table = {}
        v4("Merging: reading rules from {}".format(lookupTable))
        with open(lookupTable, 'r') as fh:
            for line in fh.readlines():
                line = line.strip()
                if line == '' or line.startswith('#'):
                    continue

                toks = line.split()
                if len(toks) != 2:
                    raise ValueError("Invalid line: '{}'".format(line))

                key, rulespec = toks
                rule = parse_merge_rule(key, rulespec)
                v4("Parsed {} to {} / {}".format(line, key, rule))
                self._table[key.upper()] = rule

    def apply(self, key, values):
        """Return the merged value for this key.

        It is not clear what to do if multiple rules match the key.
        """

        # This is complicated by the fact that it is not just an exact
        # match.
        #
        kupper = key.upper()
        try:
            rule = self._table[kupper]
        except KeyError:
            rule = None
            for rulename in self._table.keys():
                if kupper.startswith(rulename):
                    # Should we worry about multiple matches or warning
                    # the user?
                    if rule is None:
                        rule = self._table[rulename]
                    else:
                        v2("WARNING: multiple merging rules found for {}".format(key))

        if rule is None:
            # Just take the first item
            return values[0]
        else:
            v3("Header merge: for {} applying {}".format(key, rule))
            return rule.merge(values)


# End
