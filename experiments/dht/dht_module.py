import json
import os
import random
import time

from Tribler.pyipv8.ipv8.peer import Peer

from gumby.experiment import experiment_callback
from gumby.modules.community_experiment_module import IPv8OverlayExperimentModule
from gumby.modules.experiment_module import static_module

from Tribler.community.dht.community import DHTCommunity


@static_module
class DHTModule(IPv8OverlayExperimentModule):
    """
    This module contains code to manage experiments with the DHT community.
    """

    def __init__(self, experiment):
        super(DHTModule, self).__init__(experiment, DHTCommunity)
        self.start_time = 0

    def on_id_received(self):
        super(DHTModule, self).on_id_received()
        self.tribler_config.set_dispersy_enabled(False)
        self.tribler_config.set_dht_community_enabled(True)

        # Some communities can't be turned off?
        self.ipv8_community_loader.get_launcher("TriblerChainCommunity").should_launch = lambda _: False
        self.ipv8_community_loader.get_launcher("TrustChainCommunity").should_launch = lambda _: False

        self.start_time = time.time()

    def on_dispersy_available(self, dispersy):
        # Disable threadpool messages
        self.overlay._use_main_thread = True
        #self.overlay.resolve_dns_bootstrap_addresses()

    @experiment_callback
    def store(self, key, value):
        self.log_timing(self.overlay.store(key.decode('hex'), value), 'store')

    @experiment_callback
    def find(self, key):
        self.log_timing(self.overlay.find_values(key.decode('hex')), 'find')

    def log_timing(self, deferred, op):
        ts = time.time() - self.start_time
        cb = lambda _, t=ts: self.write_to_log('dht.log', '%d %s %.3f\n', ts, op, time.time() - self.start_time - t)
        eb = lambda _: self.write_to_log('dht.log', '%d %s -1', ts, op)
        deferred.addCallbacks(cb, eb)

    def write_to_log(self, fn, string, *values):
        with open(fn, 'a') as fp:
            fp.write(string % values)

