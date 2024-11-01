import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import datetime

from .local_ancillary import ignore_nans, local_stats_to_dict_fsl
from .regression import sum_squared_error

logs = []

def printAndAddToLogs(str):
    ct = datetime.datetime.now().astimezone()
    str = ct.strftime("%m/%d/%Y %H:%M:%S") + ' : ' + str
    print(str)
    logs.append(str)

def local_1(fl_ctx, data_dir_path):

    printAndAddToLogs(f"Starting validaton phase")

    computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")

    covariate_file_filepath = os.path.join(data_dir_path, "covariates.csv")
    cf = pd.read_csv(os.path.join(covariate_file_filepath))
    printAndAddToLogs(f"- Loading data from: {covariate_file_filepath}")

    data_file_filepath = os.path.join(data_dir_path, "data.csv")
    df = pd.read_csv(os.path.join(data_file_filepath))
    printAndAddToLogs(f"- Loading data from: {data_file_filepath}")

    X_vars = computation_parameters["Covariates"]
    y_vars = computation_parameters["Dependents"]
    lamb = computation_parameters["Lambda"]

    X_headers = list(X_vars.keys())
    y_headers = list(y_vars.keys())
    X_types = list(X_vars.values())
    y_types = list(y_vars.values())
    
    X = cf[X_headers]
    y = df[y_headers]

    def tryCastToInt(var):
        vartype = type(var).__name__ 
        if vartype.__contains__('bool') == False:
            try:
                int_value = int(var)
                return int_value
            except:
                pass
                return var
        else:
            return var
        
    def checkDataTypes(data,headers,vars,filename):
        for column in headers:
            try2intvar = tryCastToInt(data.iloc[0][column])
            vartype = type(try2intvar).__name__
            printAndAddToLogs(f"-- {column},{data.iloc[0][column]},{vartype},{vars[column]}") 
            if vartype.__contains__(vars[column]) == False:
                raise Exception('Values are not correct in '+filename+' file for column: '+column)
    
    printAndAddToLogs(f"- Checking: Covariates.csv") 
            
    checkDataTypes(X,X_headers,X_vars,'Covariates.csv')
        
    printAndAddToLogs(f"- Covariates.csv: data check has passed") 

    printAndAddToLogs(f"- Checking: Data.csv") 
    
    checkDataTypes(y,y_headers,y_vars,'Data.csv')
        
    printAndAddToLogs(f"- Data.csv: data check has passed") 

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

    printAndAddToLogs(f"Validation done. sending to remote...")

    result = {"input": output_dict, "cache": cache_dict, "logs": logs}

    printAndAddToLogs(f"- Sending Packet to Remote: {result}")
    
    return result

def local_2(fl_ctx, shareable):
    printAndAddToLogs(f"Remote stuff is crunched. starting next local thing...") 

    computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")

    input_list = shareable.get('result')
    cache_list = shareable.get('cache')

    X = pd.read_json(cache_list["covariates"], orient='split')
    y = pd.read_json(cache_list["dependents"], orient='split')

    biased_X = sm.add_constant(X.values)

    avg_beta_vector = input_list['input']["avg_beta_vector"]
    mean_y_global = input_list['input']["mean_y_global"]

    SSE_local, SST_local, varX_matrix_local = [], [], []

    printAndAddToLogs(f"- Crunching SSE_local, SST_local, varX_matrix_local") 

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

    printAndAddToLogs(f"Done crunching. sending back to remote...") 

    result = {"input": output_dict, "cache": cache_dict, "logs": logs}

    return result