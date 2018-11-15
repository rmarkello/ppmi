# -*- coding: utf-8 -*-
"""
Miscellaneous functions for working with derived PPMI data
"""
import numpy as np
import pandas as pd
import scipy.stats


def get_genetic_risk_score(data, odds_ratio):
    """
    Calculates genetic risk score for `data` weighted by `odds_ratio`

    Parameters
    ----------
    data : (N, G) array_like
        Allele count for `G` SNPs across `N` participants.
    odds_ratio : (G,) array_like
        Odds ratio for `G` SNPs derived from GWAS

    Returns
    -------
    gsr : (N,) np.ndarray
        Genetic risk scores for `N` participants
    """

    return np.sum(np.array(data) * np.log(np.array(odds_ratio)), axis=1)


def get_slopes(data):
    """
    Get trajectories (i.e., slopes) for participants and tests in `data`

    Performs simple regression of time (in years) against behavioral measure
    using scipy.stats.linregress (intercept automatically included). Currently
    does not support multiple regression (i.e., quadratic term).

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame as obtained by e.g., `ppmi.get_all_data()`

    Returns
    -------
    data : pandas.DataFrame
        DataFrame with all clinical-behavioral trajectories (i.e., slopes)
    """

    def get_slopes(df):
        if len(df) < 2:
            return np.nan
        x = df.AGE.get_values()
        y = df.SCORE.get_values()
        return scipy.stats.linregress(x, y)[0]

    def get_duration(df):
        if len(df) < 2:
            return np.nan
        x = df.AGE.get_values()
        return x[-1] - x[0]

    # load data, get rid of null visits and post-med UPDRS III
    data = (data.dropna(subset=['VISIT', 'VISIT_DATE'])
                .query('PAG_NAME != "NUPDRS3A"'))

    columns = ['PARTICIPANT', 'TEST', 'SLOPE', 'VISITS', 'DURATION']
    slope_df = pd.DataFrame(columns=columns)
    for test in data.TEST.unique():
        gb = (data.query(f'TEST == "{test}"')
                  .get(['PARTICIPANT', 'AGE', 'SCORE'])
                  .groupby('PARTICIPANT'))
        slope = (gb.apply(get_slopes)
                   .reset_index())
        slope.columns = ['PARTICIPANT', 'SLOPE']
        slope['TEST'] = test
        slope['VISITS'] = (gb.count()
                             .get('AGE')
                             .get_values()
                             .astype(int))
        slope['DURATION'] = (gb.apply(get_duration)
                               .get_values())

        slope_df = slope_df.append(slope, ignore_index=True, sort=True)

    return slope_df.dropna(subset=['SLOPE', 'DURATION'])[columns]
