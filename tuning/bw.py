#!/usr/bin/env python

class MixParameters(object):

    # Scaling parameters
    num_authorities = None
    num_clients = None
    num_mixes = None
    consensus_interval = None

    # Throughput parameters
    mix_bandwidth = None
    rtt = None

    # Message parameters
    message_size = None
    size_mix_descriptor = None
    size_signature = None

    # Decoy parameters
    noise_signal = None

    def __init__(self, **args):
        # initialize parameters
        self.num_authorities = args.get('num_authorities')
        self.num_clients = args.get('num_clients')
        #self.num_mixes = args.get('num_mixes')
        self.consensus_interval = args.get('consensus_interval')
        self.mix_bandwidth = args.get('mix_bandwidth')
        self.rtt = args.get('rtt')
        self.message_size = args.get('message_size')
        self.noise_signal = args.get('noise_signal')
        self.size_mix_descriptor = args.get('size_mix_descriptor')
        self.size_signature = args.get('size_signature')

    @property
    def num_mixes(self):
        return mixes_required(self)

    def __str__(self):

        fmt = "num_authorities:{}\n"
        fmt += "num_clients:\t{}\n"
        fmt += "num_mixes:\t{}\n"
        fmt += "consensus_interval:\t{}\n"
        fmt += "mix_bandwidth:\t{}\n"
        fmt += "rtt:\t\t{}\n"
        fmt += "message_size:\t{}\n"
        fmt += "size_mix_descriptor:\t{}\n"
        fmt += "size_signature:\t{}\n"
        fmt += "noise_signal:\t{}\n"
        fmt += "network_bandwidth:\t{}\n"
        fmt += "consensus_bandwidth:\t{}\n"
        fmt += "consensus_bandwidth_ratio: {}\n"
        fmt += "per_client_bandwidth:\t{}\n"
        fmt += "per_client_consensus_overhead:\t{}\n"
        fmt += "per_client_channel_bandwidth:\t{}\n"

        consensus_overhead = consensus_bandwidth_ratio(mp) * (network_bandwidth(mp) / mp.num_clients)

        return fmt.format(self.num_authorities, self.num_clients, self.num_mixes,
                self.consensus_interval, self.mix_bandwidth, self.rtt,
                self.message_size, self.size_mix_descriptor,
                self.size_signature, self.noise_signal,

                mbits(network_bandwidth(mp)),
                mbits(consensus_bandwidth(mp)),
                consensus_bandwidth_ratio(mp),
                kbits(network_bandwidth(mp) / float(mp.num_clients)),
                kbits(consensus_overhead),
                kbits(client_average_bw(mp) / (1 + mp.noise_signal) - consensus_overhead)
                )

def kbits(i):
    return "%.3f Kb/s" % (float(i) / 10**3)
def mbits(i):
    return "%.3f Mb/s" % (float(i) / 10**6)

def consensus_size(mp):
    num_mixes = mixes_required(mp)
    return num_mixes * mp.size_mix_descriptor + mp.num_authorities * mp.size_signature

def consensus_bandwidth(mp):
    num_mixes = mixes_required(mp)
    b  = 2 * num_mixes * mp.size_mix_descriptor * mp.num_authorities
    b += mp.size_signature * mp.num_authorities
    b += mp.num_clients * num_mixes * mp.size_mix_descriptor
    b += mp.num_clients * mp.size_signature * mp.num_authorities
    return b / mp.consensus_interval

# average bandwidth of all clients
def client_average_bw(mp):
    byte = 8
    decoy_overhead = (mp.noise_signal + 1)
    return decoy_overhead * (mp.message_size * byte / mp.rtt)

# network bandwidth 
def network_bandwidth(mp):
    # consensus bandwidth in bit/s
    return consensus_bandwidth(mp) + client_average_bw(mp) * mp.num_clients

# ratio consensus bandwidth / network bandwidth
def consensus_bandwidth_ratio(mp):
    return consensus_bandwidth(mp)/network_bandwidth(mp)

# number of mixes required 
def mixes_required(mp):
    # rtt is message send frequency; how often a client send/receives.
    # XXX, approx - ignores consensus overhead
    return mp.num_clients * client_average_bw(mp) / float(mp.mix_bandwidth)

# plot some values for 
#mbr(
#  // experimental values:
#  // try rtt -> 300 ms, 1 s, ..., 600 s
#  // for payload_size -> 512B, 1KB, ..., 1MB
#  // number of clients -> 5K, 10K, ..., 16 M // ha
#  bc = 512 / .3 #// low latency, short messages
#  bc = 512 / 5 #// med latency, short messages
#  bc = 5M / 600 #// high latency, large messages
#
  #// XXX How much cover traffic is needed to provide
  #// how much uncertainty? How are these units
  #// defined?
  #// bandwith cover required
  #// nsr = ratio noise / signal
  #  // experimental values
  #  // try nsr -> 0, 2, 9, 99

#Interesting things to plot
# The number of mix nodes needed for 1k, 10k, 100k, 1M, 10M 100M, 1B clients.
# For parameters selected for: 
#  low latency, short messages
#  medium latency, short messages
#  high latency, large messages

mp = MixParameters(
        num_clients = 42000,
        consensus_interval = 420,
        mix_bandwidth = .42 *10**9, # per mix
        rtt = 420,
        message_size = 42000,
        noise_signal = 0,
        num_authorities=5,
        size_mix_descriptor=100,
        size_signature=100,
        ) 

for c in [600,60*60*3]: # seconds ; consensus interval.
    mp.consensus_interval = c
    for n in [0, .5, 2, 9]: # noise / signal ratio of decoy traffic.
        mp.noise_signal = n
        for f in [60, 120, 180]: # seconds ; message frequncy.
            mp.rtt = f
            for s in [10**4, 10**5, 10**6]: # number of bytes per message
                mp.message_size = s
                for n in [10**4, 10**5, 10**6, 10**7]: # number of clients
                    mp.num_clients = n
                    print mp
# amount of bw used for consensus vs network bandwidth

