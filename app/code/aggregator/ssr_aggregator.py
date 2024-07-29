from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey
from .remote_funcs import remote_1, remote_2


class SSRAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        # Initialize stored_data to hold contributions per round and contributor
        self.stored_data = {}  # Structure: {round_number: {contributor_name: data}}

    def accept(self, shareable: Shareable, fl_ctx: FLContext) -> bool:
        """Accepts shareable contributions for aggregation.

        Args:
            shareable: The shareable data from a contributor.
            fl_ctx: The federated learning context.

        Returns:
            bool: True indicating acceptance of the shareable data.
        """
        contribution_round = fl_ctx.get_prop(key="CURRENT_ROUND", default=None)
        contributor_name = shareable.get_peer_prop(
            key=ReservedKey.IDENTITY_NAME, default=None)

        print(
            f"Aggregator received contribution from {contributor_name}"
            f" for round {contribution_round}"
        )

        if contribution_round is None or contributor_name is None:
            return False  # Could log a warning/error here as well

        if contribution_round not in self.stored_data:
            self.stored_data[contribution_round] = {}

        # It's assumed shareable.get("result", {}) correctly fetches the data dict
        self.stored_data[contribution_round][contributor_name] = shareable.get(
            "result", {})
        return True

    def aggregate(self, fl_ctx: FLContext) -> Shareable:
        """Aggregates contributions for the current round into results.

        Args:
            fl_ctx: The federated learning context.

        Returns:
            Shareable: A shareable containing results.
        """
        contribution_round = fl_ctx.get_prop(key="CURRENT_ROUND", default=None)
        data_for_aggregation = []

        if contribution_round in self.stored_data and self.stored_data[contribution_round]:
            for data in self.stored_data[contribution_round].values():
                data_for_aggregation.append(data)

            # get the computation parameters
            computation_parameters = fl_ctx.get_prop("COMPUTATION_PARAMETERS")

            if(contribution_round == 0):
                remote_input = remote_1(data_for_aggregation)
                outgoing_shareable = Shareable()
                outgoing_shareable['result'] = remote_input
                return outgoing_shareable
            if(contribution_round == 1):
                cache = fl_ctx.get_prop(key="REMOTE_CACHE")
                remote_input = remote_2(data_for_aggregation, cache)
                outgoing_shareable = Shareable()
                outgoing_shareable['result'] = remote_input
                return outgoing_shareable
            else:
                return Shareable()  # Return an empty Shareable if no data to aggregate
