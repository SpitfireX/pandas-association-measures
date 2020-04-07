"""
Association measures are mathematical formulae that interpret cooccurrence frequency data.

http://www.collocations.de/AM/index.html
"""


import pandas as pd
import numpy as np
from .binomial import choose as binomial
from .frequencies import expected_frequencies


choose = np.vectorize(binomial)  # pylint: disable=invalid-name


def z_score(df):
    """
    Calculate z-score

    :param pandas.DataFrame df: Pandas Dataframe containing O11 and E11
    :return: pandas.Series containing the Z-Score for each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['O11', 'E11']).all()):
        expected_frequencies(df)

    res = (df['O11'] - df['E11']) / np.sqrt(df['E11'])

    return pd.Series(data=res)


def t_score(df):
    """
    Calculate t-score

    :param pandas.DataFrame df: Pandas Dataframe containing O11 and E11
    :return: pandas.Series containing the T-Score for each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['O11', 'E11']).all()):
        expected_frequencies(df)

    res = (df['O11'] - df['E11']) / np.sqrt(df['O11'])

    return pd.Series(data=res)


def mutual_information(df):
    """
    Calculate Mutual Information

    :param pandas.DataFrame df: Pandas Dataframe containing O11 and E11
    :return: pandas.Series containing the Mutual Information score for
    each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['O11', 'E11']).all()):
        expected_frequencies(df)

    diff = df['O11'].replace(0, np.nan) / df['E11'].replace(0, np.nan)
    res = np.log10(diff.replace(0.0, np.nan))

    return pd.Series(data=res)


def dice(df):
    """
    Calculate Dice coefficient

    :param pandas.DataFrame df: Pandas Dataframe containing O11, O12, O21
    :return: pandas.Series containing the Dice coefficient for each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['O11', 'E11']).all()):
        expected_frequencies(df)

    res = (2 * df['O11']) / (2 * df['O11'] + df['O12'] + df['O21'])

    return pd.Series(data=res)


def log_likelihood(df, signed=True):
    """
    Calculate log-likelihood

    :param pandas.DataFrame df: Pandas Dataframe containing O11, O12,
    O21, O22, E11, E12, E21 and E22
    :return: pandas.Series containing the log-likelihood score for each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['O11', 'O12', 'O21', 'O22', 'E11', 'E12', 'E21', 'E22']).all()):
        expected_frequencies(df)

    with np.errstate(divide='ignore', invalid='ignore'):
        ii = df['O11'] * np.log(df['O11'] / df['E11'].replace(0, np.nan))
        ij = df['O12'] * np.log(df['O12'] / df['E12'].replace(0, np.nan))
        ji = df['O21'] * np.log(df['O21'] / df['E21'].replace(0, np.nan))
        jj = df['O22'] * np.log(df['O22'] / df['E22'].replace(0, np.nan))

    res = 2 * pd.concat([ii, ij, ji, jj], axis=1).sum(1)
    if signed:
        res = np.sign(df['O11'] - df['E11']) * res

    return pd.Series(data=res)


def hypergeometric_likelihood(df):
    """
    Calculate hypergeometric-likelihood

    :param pandas.DataFrame df: Pandas Dataframe containing O11, O12,
    O21, O22, E11, E12, E21 and E22
    :return: pandas.Series containing the hypergeometric-likelihood score for each token
    :rtype: pandas.Series
    """

    df = df.copy()
    if not (df.columns.isin(['N', 'O11', 'O12', 'O21', 'O22', 'E11', 'E12', 'E21', 'E22']).all()):
        expected_frequencies(df)

    # TODO: Is this correct?
    # looks good but does not return any results except Inf / -Inf
    # probably an error in choose?
    res = (
        choose(df['O11'] + df['O21'], df['O11']) *
        choose(df['O12'] + df['O22'], df['O12'])
    ) / choose(df['N'], df['O11'] + df['O12'])

    return pd.Series(data=res)


def log_ratio(df):

    df = df.copy()
    if not (df.columns.isin(['N', 'O11', 'O12', 'O21', 'O22', 'E11', 'E12', 'E21', 'E22']).all()):
        expected_frequencies(df)

    C1 = df['O11'] + df['O21']
    C2 = df['O12'] + df['O22']
    ratio = df['O11'] / C1 / (df['O12'] / C2)

    return pd.Series(data=np.log2(ratio))


def calculate_measures(df, measures=None, inplace=True):
    """
    Calculate a list of association measures. Defaults to all available measures.

    :param pandas.DataFrame df: Dataframe with reasonably-named freq. signature
    :param measures list: names of AMs (or AMs)
    :return: pandas.DataFrame with association measures
    :rtype: pandas.DataFrame
    """

    # inplace?
    if not inplace:
        df_loc = df.copy()
    else:
        df_loc = df

    # implemented measures
    ams_all = {
        'z_score': z_score,
        't_score': t_score,
        'dice': dice,
        'log_likelihood': log_likelihood,
        'mutual_information': mutual_information,
        'log_ratio': log_ratio,
        # 'hypergeometric_likelihood': hypergeometric_likelihood
    }

    # check for expected frequencies
    if not (df.columns.isin(['E11', 'E12', 'E21', 'E22']).all()):
        expected_frequencies(df_loc, inplace=True)

    # select measures
    if measures is not None:
        if type(measures[0]) == str:
            measures = [ams_all[k] for k in measures if k in ams_all.keys()]
    else:
        measures = [ams_all[k] for k in ams_all.keys()]

    # calculate measures
    for measure in measures:
        df[measure.__name__] = measure(df_loc)

    return df
