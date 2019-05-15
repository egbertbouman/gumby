import binascii
import hashlib
import os
import random
import time

from collections import defaultdict

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

from gumby.experiment import experiment_callback
from gumby.modules.community_experiment_module import IPv8OverlayExperimentModule
from gumby.modules.experiment_module import static_module

from Tribler.community.triblertunnel.community import TriblerTunnelCommunity
from Tribler.pyipv8.ipv8.messaging.anonymization.pex import PexCommunity, PexEndpointAdapter
from Tribler.pyipv8.ipv8.peerdiscovery.network import Network
from Tribler.pyipv8.ipv8.peerdiscovery.discovery import RandomWalk


@static_module
class PexModule(IPv8OverlayExperimentModule):

    def __init__(self, experiment):
        super(PexModule, self).__init__(experiment, TriblerTunnelCommunity)
        self.pex_ep_adapter = None
        self.pex = {}
        self.counter = 0

    def on_id_received(self):
        super(PexModule, self).on_id_received()
        self.tribler_config.set_tunnel_community_enabled(True)
        self.autoplot_create('pex_communities', 'num_communities')
        self.autoplot_create('intro_points', 'num_intro_points')

    def on_ipv8_available(self, _):
        self.pex_ep_adapter = PexEndpointAdapter(self.ipv8.endpoint)
        self.overlay.resolve_dns_bootstrap_addresses()

    @experiment_callback
    def start_pex(self, loops, max_time):
        self.counter += 1
        self._start_pex(int(loops), float(max_time))

    def _start_pex(self, loops, max_time):
        if loops <= 0:
            return

        info_hash = hashlib.sha1(str(self.counter) + str(loops)).digest()
        seeder_pk = binascii.b2a_hex(os.urandom(20))
        community = PexCommunity(self.overlay.my_peer, self.pex_ep_adapter, Network(), info_hash=info_hash)
        self.ipv8.overlays.append(community)
        self.ipv8.strategies.append((RandomWalk(community, target_interval=5), 10))
        self.pex[info_hash] = community
        self.pex[info_hash].start_announce(seeder_pk)
        self.write_stats()

        loops -= 1
        t_sleep = random.uniform(0.0, max_time)
        reactor.callLater(t_sleep, self._start_pex, loops, max_time)

    @experiment_callback
    def stop_pex(self, loops, max_time):
        self._stop_pex(int(loops), float(max_time))

    def _stop_pex(self, loops, max_time):
        if loops <= 0:
            return

        info_hash = random.sample(self.pex.keys(), 1)[0]
        seeder_pk = random.sample(self.pex[info_hash].intro_points_for, 1)[0]
        pex = self.pex.get(info_hash)
        pex.stop_announce(seeder_pk)
        if pex.done:
            self.pex.pop(info_hash, None)
            self.ipv8.overlays.remove(pex)
            self.ipv8.strategies = [t for t in self.ipv8.strategies if t[0].overlay != pex]
            pex.unload()
        self.write_stats()

        loops -= 1
        t_sleep = random.uniform(0.0, max_time)
        reactor.callLater(t_sleep, self._stop_pex, loops, max_time)

    def write_stats(self):
        self.autoplot_add_point('pex_communities', len(self.pex))

        intro_points = 0
        for pex in self.pex.values():
            intro_points += (len(pex.get_intro_points()) - 1)
        self.autoplot_add_point('intro_points', intro_points)

