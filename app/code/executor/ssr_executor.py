from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.fl_context import FLContext
from nvflare.apis.shareable import Shareable
from nvflare.apis.signal import Signal

import os
from .output import generateOutput

from .local_funcs import local_1, local_2

class SSRExecutor(Executor):
    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:

        if task_name == "local1":
            data_dir_path = get_data_dir_path(fl_ctx)
            result = local_1(fl_ctx, data_dir_path)
            site = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)
            outgoing_shareable = Shareable()
            outgoing_shareable["result"] = result
            outgoing_shareable["result"]["site"] = site
            return outgoing_shareable
        
        if task_name == "local2":
            data_dir_path = get_data_dir_path(fl_ctx)
            result = local_2(fl_ctx, shareable)
            outgoing_shareable = Shareable()
            outgoing_shareable["result"] = result
            outgoing_shareable["result"]["site"] = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)
            return outgoing_shareable
        
        if task_name == "local3":
            results_dir = get_results_dir_path(fl_ctx)
            print(f"\nSaving results to: {results_dir}\n")
            save_results_to_file(shareable, 'index.html', fl_ctx)
    
def save_results_to_file(results: dict, file_name: str, fl_ctx: FLContext):
    results_dir = get_results_dir_path(fl_ctx)
    results_file = os.path.join(results_dir, file_name)
    with open(results_file, "w") as f:
        generateOutput(results_file, results['result']['output'])


def get_results_dir_path(fl_ctx: FLContext) -> str:
    """
    Determines the appropriate results directory path for the federated learning application by checking
    if in production, simulator, or POC (Proof of Concept) mode.
    """

    # Define paths for production (from environment), simulator, and POC modes.
    job_id = fl_ctx.get_job_id()
    site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)

    production_path = os.getenv("RESULTS_DIR")
    simulator_base_path = os.path.abspath(
        os.path.join(os.getcwd(), "../../../test_results"))
    poc_base_path = os.path.abspath(os.path.join(
        os.getcwd(), "../../../../test_results"))
    simulator_path = os.path.join(simulator_base_path, job_id, site_name)
    poc_path = os.path.join(poc_base_path, job_id, site_name)

    # Check for the environment path first, then simulator, and lastly POC path.
    if production_path:
        return production_path
    if os.path.exists(simulator_base_path):
        os.makedirs(simulator_path, exist_ok=True)
        return simulator_path
    if os.path.exists(poc_base_path):
        os.makedirs(poc_path, exist_ok=True)
        return poc_path

    # Raise an error if no path is found.
    raise FileNotFoundError("Results directory path could not be determined.")


def get_data_dir_path(fl_ctx: FLContext) -> str:
    """
    Determines the appropriate data directory path for the federated learning application by checking
    if in production, simulator, or poc mode.
    """

    # Define paths for production (from environment), simulator, and POC modes.
    site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)


    production_path = os.getenv("DATA_DIR")
    simulator_path = os.path.abspath(os.path.join(os.getcwd(), "../../../test_data", site_name))
    poc_path = os.path.abspath(os.path.join(os.getcwd(), "../../../../test_data", site_name))

    # Check for the environment path first, then simulator, and lastly POC path.
    if production_path:
        return production_path
    if os.path.exists(simulator_path):
        return simulator_path
    if os.path.exists(poc_path):
        return poc_path

    # Raise an error if no path is found.
    raise FileNotFoundError("Data directory path could not be determined.")


