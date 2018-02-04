#!/usr/bin/env python

class MixParameters(object):

    # Scaling parameters
    n_authorities = None
    n_clients = None
    n_mixes = None
    consensus_time = None

    # Throughput parameters
    mix_bandwidth = None
    rtt = None

    # Message parameters
    message_size = None
    desc_size = None
    sig_size = None

    # Decoy parameters
    noise_signal = None

    def __init__(self, **args):
        # initialize parameters
        self.n_authorities = args.get('n_authorities')
        self.n_clients = args.get('n_clients')
        #self.num_mixes = args.get('num_mixes')
        self.consensus_time = args.get('consensus_time')
        self.mix_bandwidth = args.get('mix_bandwidth')
        self.rtt = args.get('rtt')
        self.message_size = args.get('message_size')
        self.noise_signal = args.get('noise_signal')
        self.desc_size = args.get('desc_size')
        self.sig_size = args.get('sig_size')

    @property
    def n_mixes(self):
        return mixes_required(self)

    def __str__(self):

        fmt = "n_authorities:{}\n"
        fmt += "n_clients:\t{}\n"
        fmt += "n_mixes:\t{}\n"
        fmt += "consensus_time:\t{}\n"
        fmt += "mix_bandwidth:\t{}\n"
        fmt += "rtt:\t\t{}\n"
        fmt += "message_size:\t{}\n"
        fmt += "consensus_size:\t{}\n"
        fmt += "consensus_mb:\t{}\n"
        fmt += "network_mb:\t{}\n"
        fmt += "desc_size:\t{}\n"
        fmt += "sig_size:\t{}\n"
        fmt += "noise_signal:\t{}\n"
        fmt += "network_bandwidth:\t{}\n"
        fmt += "consensus_bandwidth:\t{}\n"
        fmt += "per_client_bandwidth:\t{}\n"
        fmt += "per_client_consensus_overhead:\t{}\n"
        fmt += "per_client_channel_bandwidth:\t{}\n"

        consensus_overhead = consensus_bandwidth_ratio(mp) * (network_bandwidth(mp) / mp.n_clients)

        def seconds(i):
            return "%.3f s" % i
        def byts(i):
            return "%.3f B" % i
        def kbyte(i):
            return "%.3f kB" % (float(i) / 2**10)
        def mbyte(i):
            return "%.3f MB" % (float(i) / 2**20)
        def gbyte(i):
            return "%.3f GB" % (float(i) / 2**30)
        def tbyte(i):
            return "%.3f TB" % (float(i) / 2**40)
        def kbits(i):
            return "%.3f Kbit" % (float(i) / 10**3)
        def mbits(i):
            return "%.3f Mbit" % (float(i) / 10**6)

        return fmt.format(self.n_authorities, self.n_clients, self.n_mixes,
                seconds(self.consensus_time),
                mbits(self.mix_bandwidth),
                seconds(self.rtt),
                kbyte(self.message_size),
                kbyte(consensus_size(mp)),
                gbyte(consensus_size(mp) * mp.n_clients),
                gbyte(network_bandwidth(mp)),
                byts(self.desc_size),
                byts(self.sig_size),
                self.noise_signal,
                mbits(network_bandwidth(mp)),
                mbits(consensus_bandwidth(mp)),
                kbits(network_bandwidth(mp) / float(mp.n_clients)),
                kbits(consensus_overhead),
                kbits(client_average_bw(mp) / (1 + mp.noise_signal) - consensus_overhead)
                )

def consensus_size(mp):
    n_mixes = mixes_required(mp)
    return n_mixes * mp.desc_size + mp.n_authorities * mp.sig_size

def consensus_bandwidth(mp):
    n_mixes = mixes_required(mp)
    b  = 2 * n_mixes * mp.desc_size * mp.n_authorities
    b += mp.sig_size * mp.n_authorities
    b += mp.n_clients * n_mixes * mp.desc_size
    b += mp.n_clients * mp.sig_size * mp.n_authorities
    return b / mp.consensus_time

# average bandwidth of all clients
def client_average_bw(mp):
    byte = 8
    decoy_overhead = (mp.noise_signal + 1)
    return decoy_overhead * (mp.message_size * byte / mp.rtt)

# network bandwidth
def network_bandwidth(mp):
    # consensus bandwidth in bit/s
    return consensus_bandwidth(mp) + client_average_bw(mp) * mp.n_clients

# ratio consensus bandwidth / network bandwidth
def consensus_bandwidth_ratio(mp):
    return consensus_bandwidth(mp)/network_bandwidth(mp)

# number of mixes required
def mixes_required(mp):
    # rtt is message send frequency; how often a client send/receives.
    # XXX, approx - ignores consensus overhead
    return mp.n_clients * client_average_bw(mp) / float(mp.mix_bandwidth)

mp = MixParameters(
        mix_bandwidth = 42 *10**7, # per mix throughput
        message_size = 50000,
        noise_signal = 0,
        n_authorities=9,
        desc_size=32+32+3*32+10+2, #identity, link, and mix keys for 3 epochs, 10 bytes of addresses
        sig_size=100,
        )

# XXX pass by argument or config
for c in [60*60*3]: # seconds ; consensus interval.
    mp.consensus_time = c
    for n in [0, .5, 2, 9]: # noise / signal ratio of decoy traffic.
        mp.noise_signal = n
        for f in [.3, 1, 5, 60, 120, 600]: # seconds ; message frequncy.
            mp.rtt = f
            for s in [5*10**4]: # number of bytes per message
                mp.message_size = s
                for n in [10**4, 10**5, 10**6, 10**8]: # number of clients
                    mp.n_clients = n
                    print mp
