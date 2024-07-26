#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script includes the remote computations for single-shot ridge
regression with decentralized statistic calculation
"""
import numpy as np
import scipy as sp
from itertools import repeat
from .remote_ancillary import get_stats_to_dict
from .regression import t_to_p


def remote_1(input):
    """Computes the global beta vector, mean_y_global & dof_global

    Args:
        args (dictionary): {"input": {
                                "beta_vector_local": list/array,
                                "mean_y_local": list/array,
                                "count_local": int,
                                "computation_phase": string
                                },
                            "cache": {}
                            }

    Returns:
        computation_output (json) : {"output": {
                                        "avg_beta_vector": list,
                                        "mean_y_global": ,
                                        "computation_phase":
                                        },
                                    "cache": {
                                        "avg_beta_vector": ,
                                        "mean_y_global": ,
                                        "dof_global":
                                        },
                                    }

    """
    X_labels = input[0]['input']["X_labels"]
    y_labels = input[0]['input']["y_labels"]

    all_local_stats_dicts = []

    all_local_stats_dicts = [
        site['input']["local_stats_dict"] for site in input
    ]

    avg_beta_vector = np.average([
        np.array(site['input']["beta_vector_local"]) for site in input
    ],axis=0)

    mean_y_local = [site['input']["mean_y_local"] for site in input]
    count_y_local = [
        np.array(site['input']["count_local"]) for site in input
    ]
    mean_y_global = np.array(mean_y_local) * np.array(count_y_local)
    mean_y_global = np.sum(mean_y_global, axis=0) / np.sum(count_y_local,
                                                           axis=0)

    dof_global = sum(count_y_local) - avg_beta_vector.shape[1]

    output_dict = {
        "avg_beta_vector": avg_beta_vector.tolist(),
        "mean_y_global": mean_y_global.tolist(),
        "computation_phase": 'remote_1'
    }

    cache_dict = {
        "avg_beta_vector": avg_beta_vector.tolist(),
        "mean_y_global": mean_y_global.tolist(),
        "dof_global": dof_global.tolist(),
        "X_labels": X_labels,
        "y_labels": y_labels,
        "local_stats_dict": all_local_stats_dicts
    }

    computation_output = {"input": output_dict, "cache": cache_dict}

    return computation_output


def remote_2(input, cache):
    """
    Computes the global model fit statistics, r_2_global, ts_global, ps_global

    Args:
        args (dictionary): {"input": {
                                "SSE_local": ,
                                "SST_local": ,
                                "varX_matrix_local": ,
                                "computation_phase":
                                },
                            "cache":{},
                            }

    Returns:
        computation_output (json) : {"output": {
                                        "avg_beta_vector": ,
                                        "beta_vector_local": ,
                                        "r_2_global": ,
                                        "ts_global": ,
                                        "ps_global": ,
                                        "dof_global":
                                        },
                                    "success":
                                    }
    Comments:
        Generate the local fit statistics
            r^2 : goodness of fit/coefficient of determination
                    Given as 1 - (SSE/SST)
                    where   SSE = Sum Squared of Errors
                            SST = Total Sum of Squares
            t   : t-statistic is the coefficient divided by its standard error.
                    Given as beta/std.err(beta)
            p   : two-tailed p-value (The p-value is the probability of
                  seeing a result as extreme as the one you are
                  getting (a t value as large as yours)
                  in a collection of random data in which
                  the variable had no effect.)

    """
    X_labels = cache["X_labels"]
    y_labels = cache["y_labels"]

    all_local_stats_dicts = cache["local_stats_dict"]

    avg_beta_vector = cache["avg_beta_vector"]
    dof_global = cache["dof_global"]

    SSE_global = sum(
        [np.array(site['input']["SSE_local"]) for site in input])
    SST_global = sum(
        [np.array(site['input']["SST_local"]) for site in input])
    varX_matrix_global = sum([
        np.array(site['input']["varX_matrix_local"]) for site in input
    ])

    r_squared_global = 1 - (SSE_global / SST_global)
    MSE = SSE_global / np.array(dof_global)

    ts_global = []
    ps_global = []

    for i in range(len(MSE)):
        var_covar_beta_global = MSE[i] * sp.linalg.inv(varX_matrix_global[i])
        se_beta_global = np.sqrt(var_covar_beta_global.diagonal())
        ts = (avg_beta_vector[i] / se_beta_global).tolist()
        ps = t_to_p(ts, dof_global[i])
        ts_global.append(ts)
        ps_global.append(ps)

    # Block of code to print local stats as well
    sites = [site['site'] for site in input]

    a_dict = [{key: value
              for key, value in zip(sites, stats_dict)}
              for stats_dict in all_local_stats_dicts]

    # Block of code to print just global stats
    keys1 = [
        "Coefficient", "R Squared", "t Stat", "P-value", "Degrees of Freedom",
        "covariate_labels"
    ]

    X_labels.insert(0, 'const')

    global_dict_list = get_stats_to_dict(keys1, avg_beta_vector,
                                         r_squared_global, ts_global,
                                         ps_global, dof_global,
                                         repeat(X_labels, len(y_labels)))

    # Print Everything
    keys2 = ["ROI", "global_stats", "local_stats"]
    dict_list = get_stats_to_dict(keys2, y_labels, global_dict_list, a_dict)

    computation_output = {"output": dict_list}

    return computation_output
