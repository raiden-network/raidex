from raidex.raidex_node.architecture.event_architecture import Processor, dispatch_state_changes
from raidex.raidex_node.trader.listener.events import RaidenListenerEvent
from raidex.raidex_node.trader.listener.filter import RaidenEventFilter


class RaidenListener(Processor):

    def __init__(self, trader):
        super(RaidenListener, self).__init__(RaidenListenerEvent)
        self.trader = trader
        self.event_filters = list()

    def new_raiden_event(self, event):
        state_changes = list()
        copied_list = self.event_filters.copy()
        for event_filter in copied_list:
            state_change = event_filter.process(event)
            if state_change is not None:
                state_changes.append(state_change)
                self.event_filters.remove(event_filter)

        dispatch_state_changes(state_changes)

    def add_event_filter(self, new_filter: RaidenEventFilter):
        self.event_filters.append(new_filter)
