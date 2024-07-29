from nvflare.apis.impl.controller import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable

import os
import json


class SSRWorkflow(Controller):
    def __init__(
        self,
        aggregator_id="aggregator",
        min_clients: int = 2,
        num_rounds: int = 2,
        start_round: int = 0,
        wait_time_after_min_received: int = 10,
        train_timeout: int = 0,
        ignore_result_error: bool = False,
        task_check_period: float = 0.5,
        persist_every_n_rounds: int = 1,
        snapshot_every_n_rounds: int = 1,
    ):
        super().__init__()
        self.aggregator_id = aggregator_id
        self.aggregator = None
        self._train_timeout = train_timeout
        self._min_clients = min_clients
        self._num_rounds = num_rounds
        self._start_round = start_round
        self._wait_time_after_min_received = wait_time_after_min_received
        self._ignore_result_error = ignore_result_error
        self._task_check_period = task_check_period
        self._persist_every_n_rounds = persist_every_n_rounds
        self._snapshot_every_n_rounds = snapshot_every_n_rounds
        pass

    def start_controller(self, fl_ctx: FLContext) -> None:
        self.aggregator = self._engine.get_component(self.aggregator_id)

    def stop_controller(self, fl_ctx: FLContext):
        pass

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext) -> None:
        fl_ctx.set_prop(key="CURRENT_ROUND", value=0)
        fl_ctx.set_prop(key="REMOTE_CACHE", value={})

        # load parameters.json and set to the context that will be shared with clients
        parameters_file_path = self.get_parameters_file_path()
        computation_parameters = self.load_computation_parameters(
            parameters_file_path)
        
        self.validate_parameters(computation_parameters)

        fl_ctx.set_prop(key="COMPUTATION_PARAMETERS",
                        value=computation_parameters, private=False, sticky=True)

        # create the initial local task
        local1 = Task(
            name="local1",
            data=Shareable(),
            props={},
            timeout=self._train_timeout,
            # before_task_sent_cb=self._prepare_train_task_data,
            result_received_cb=self._accept_site_result,
        )

        # broadcast the task to all clients and await their responses
        self.broadcast_and_wait(
            task=local1,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

        # once the all responses are returned, start the initial remote aggregation process
        self.log_info(fl_ctx, "Start aggregation.")
        aggr_shareable = self.aggregator.aggregate(fl_ctx)
        # Get and Set values for Aggregator (Remote) persistent data (Cache)
        fl_ctx.set_prop(key="REMOTE_CACHE", value=aggr_shareable['result']['cache'])
        self.log_info(fl_ctx, "Aggregation Finished.")

        fl_ctx.set_prop(key="CURRENT_ROUND", value=1)

        aggr_shareable['cache'] = fl_ctx.get_prop("LOCAL_CACHE")

        # create the local2 task
        local2 = Task(
            name="local2",
            data=aggr_shareable,
            props={},
            timeout=self._train_timeout,
            # before_task_sent_cb=self._prepare_train_task_data,
            result_received_cb=self._accept_site_result,
        )

        # broadcast the local2 task to all clients
        self.broadcast_and_wait(
            task=local2,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

        # once the all responses are returned, start the 2nd remote aggregation process
        self.log_info(fl_ctx, "Start aggregation.")
        aggr_shareable = self.aggregator.aggregate(fl_ctx)
        # No more need for persistent data (Cache) values from here on...
        self.log_info(fl_ctx, "Aggregation Finished.")

        # create a task to accept the results of the 2nd remote process
        local3 = Task(
            name="local3",
            data=aggr_shareable,
            props={},
            timeout=self._train_timeout,
        )

        # broadcast the task to all clients to generate the html based run results
        self.broadcast_and_wait(
            task=local3,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

    def _accept_site_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        accepted = self.aggregator.accept(client_task.result, fl_ctx)
        result = client_task.result['result']
        # get and set persistent data (cache) for locals
        fl_ctx.set_prop(key="LOCAL_CACHE",value=result['cache'])
        return accepted

    def process_result_of_unknown_task(self, task: Task, fl_ctx: FLContext) -> None:
        pass

    def get_parameters_file_path(self) -> str:
        """
        Determines the appropriate data directory path for the federated learning application by checking
        if in production, simulator or poc mode.
        """

        production_path = os.getenv("PARAMETERS_FILE_PATH")
        simulator_path = os.path.abspath(os.path.join(
            os.getcwd(), "../test_data", "server", "parameters.json"))
        poc_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../../test_data", "server", "parameters.json"))

        print("\n\n")
        print(f"production_path: {production_path}")
        print(f"simulator_path: {simulator_path}")
        print(f"poc_path: {poc_path}")
        print("\n\n")
        
        if production_path:
            return production_path
        if os.path.exists(simulator_path):
            return simulator_path
        elif os.path.exists(poc_path):
            return poc_path
        else:
            raise FileNotFoundError(
                "parameters file path could not be determined.")

    def load_computation_parameters(self, parameters_file_path: str):
        with open(parameters_file_path, "r") as file:
            return json.load(file)

    def validate_parameters(self, parameters: dict) -> None:
        try:
            if 'y_headers' not in parameters:
                raise ValueError("Validation Error: The key 'y_headers' is missing in the parameters.")
            if not isinstance(parameters['y_headers'], (list)):
                raise ValueError("Validation Error: The value of 'y_headers' must be a number.")
            if 'X_headers' not in parameters:
                raise ValueError("Validation Error: The key 'X_headers' is missing in the parameters.")
            if not isinstance(parameters['X_headers'], (list)):
                raise ValueError("Validation Error: The value of 'X_headers' must be a number.")
            if 'Lambda' not in parameters:
                raise ValueError("Validation Error: The key 'Lambda' is missing in the parameters.")
            if not isinstance(parameters['Lambda'], (int)):
                raise ValueError("Validation Error: The value of 'Lambda' must be a number.")
        except ValueError as e:
            raise ValueError(f"Error validating parameters: {e}")
