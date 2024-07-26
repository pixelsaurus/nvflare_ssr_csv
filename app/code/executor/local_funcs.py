import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import ujson as json

from .local_ancillary import ignore_nans, local_stats_to_dict_fsl
from .regression import sum_squared_error

def local_1(fl_ctx, data_dir_path):
    computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")

    data_file_filepath = os.path.join(data_dir_path, "data.csv")
    covariate_file_filepath = os.path.join(data_dir_path, "covariates.csv")

    df = pd.read_csv(os.path.join(data_file_filepath))
    print(f"loading data from: {data_file_filepath}")
    cf = pd.read_csv(os.path.join(covariate_file_filepath))
    print(f"loading data from: {covariate_file_filepath}")

    X_headers = computation_parameters["X_headers"]
    y_headers = computation_parameters["y_headers"]
    lamb = computation_parameters["Lambda"]
    
    X = cf[X_headers]
    y = df[y_headers]

    t = local_stats_to_dict_fsl(X, y)
    beta_vector, local_stats_list, meanY_vector, lenY_vector = t

    output_dict = {
        "beta_vector_local": beta_vector,
        "mean_y_local": meanY_vector,
        "count_local": lenY_vector,
        "X_labels": X_headers,
        "y_labels": y_headers,
        "local_stats_dict": local_stats_list,
    }

    cache_dict = {
        "covariates": X.to_json(orient='split'),
        "dependents": y.to_json(orient='split'),
        "lambda": lamb
    }

    result = {"input": output_dict, "cache": cache_dict}
    
    return result

def local_2(fl_ctx, shareable):
    computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")

    input_list = shareable.get('result')
    cache_list = shareable.get('cache')

    X = pd.read_json(cache_list["covariates"], orient='split')
    y = pd.read_json(cache_list["dependents"], orient='split')

    biased_X = sm.add_constant(X.values)

    avg_beta_vector = input_list['input']["avg_beta_vector"]
    mean_y_global = input_list['input']["mean_y_global"]

    SSE_local, SST_local, varX_matrix_local = [], [], []

    for index, column in enumerate(y.columns):
        curr_y = y[column]

        X_, y_ = ignore_nans(biased_X, curr_y)

        SSE_local.append(sum_squared_error(X_, y_, avg_beta_vector[index]))
        SST_local.append(
            np.sum(np.square(np.subtract(y_, mean_y_global[index]))))

        varX_matrix_local.append(np.dot(X_.T, X_).tolist())

    output_dict = {
        "SSE_local": SSE_local,
        "SST_local": SST_local,
        "varX_matrix_local": varX_matrix_local,
    }

    cache_dict = {}

    result = {"input": output_dict, "cache": cache_dict}

    return result