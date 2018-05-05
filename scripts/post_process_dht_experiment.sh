#!/bin/bash

# Parse statistics about the tunnel community
gumby/experiments/dht/parse_dht_statistics.py .

graph_process_guard_data.sh

# Run the regular Dispersy message extraction script
# post_process_dispersy_experiment.sh
