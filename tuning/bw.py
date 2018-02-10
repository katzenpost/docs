#!/usr/bin/env python

class MixParameters(object):
    """ MixParameters: A class to contain and estimate mix parameters.
    """

    # Scaling parameters
    n_authorities = None
    n_clients = None
    consensus_time = None

    # Throughput parameters
    mix_bandwidth = None
    lambda_p = None

    # Message parameters
    message_size = None
    desc_size = None
    sig_size = None

    # Decoy traffic parameters, as a ratio of noise to signal
    # XXX: would be useful to break this into loop messages and drop messages.
    # e.g. a noise_signal value of 2 means 2 decoy messages for every message.
    noise_signal = None

    def __init__(self, **args):
        # initialize parameters from keyword arguments or leave
        # defaulted to None if not supplied.
        self.n_authorities = args.get('n_authorities')
        self.n_clients = args.get('n_clients')
        self.consensus_time = args.get('consensus_time')
        self.mix_bandwidth = args.get('mix_bandwidth')
        self.lambda_p = args.get('lambda_p')
        self.message_size = args.get('message_size')
        self.noise_signal = args.get('noise_signal')
        self.desc_size = args.get('desc_size')
        self.sig_size = args.get('sig_size')

    @property
    def n_mixes(self):
        """ the number of mixes needed given the network parameters """
        return self.mixes_required

    def __str__(self):

        fmt = "n_authorities:{}\n"
        fmt += "n_clients:\t{}\n"
        fmt += "n_mixes:\t{}\n"
        fmt += "consensus_time:\t{}\n"
        fmt += "mix_bandwidth:\t{}\n"
        fmt += "lambda_p:\t{}\n"
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

        def seconds(i):
            """ format i as seconds """
            return "%.3f s" % float(i)
        def byts(i):
            """ format i as bytes """
            return "%.3f B" % float(i)
        def kbyte(i):
            """ format i as kilobytes """
            return "%.3f kB" % (float(i) / 2**10)
        def mbyte(i):
            """ format i as megabytes """
            return "%.3f MB" % (float(i) / 2**20)
        def gbyte(i):
            """ format i as gigabytes """
            return "%.3f GB" % (float(i) / 2**30)
        def tbyte(i):
            """ format i as terabytes"""
            return "%.3f TB" % (float(i) / 2**40)
        def kbits(i):
            """ format i as kilobits"""
            return "%.3f Kbit" % (float(i) / 10**3)
        def mbits(i):
            """ format i as megabits"""
            return "%.3f Mbit" % (float(i) / 10**6)
        def gbits(i):
            """ format i as gigabits"""
            return "%.3f Gbit" % (float(i) / 10**9)

        return fmt.format(self.n_authorities, self.n_clients, self.n_mixes,
                          seconds(self.consensus_time),
                          mbits(self.mix_bandwidth),
                          seconds(self.lambda_p),
                          kbyte(self.message_size),
                          kbyte(self.consensus_size),
                          gbyte(self.consensus_size * self.n_clients),
                          gbyte(self.network_bandwidth),
                          byts(self.desc_size),
                          byts(self.sig_size),
                          self.noise_signal,
                          gbits(self.network_bandwidth),
                          mbits(self.consensus_bandwidth),
                          kbits(self.network_bandwidth / float(self.n_clients)),
                          kbits(self.consensus_overhead),
                          kbits(self.client_average_bw /
                                (1 + self.noise_signal) - self.consensus_overhead))

    @property
    def client_average_bw(self):
        """ Returns the average bitrate of a mix client in bits/second """
        byte = 8
        decoy_overhead = (self.noise_signal + 1)
        return decoy_overhead * (self.message_size * byte / self.lambda_p)

    @property
    def consensus_bandwidth(self):
        """ Returns the bitrate consensus computation and distribution requires in bits/second """
        c_bw = 2 * self.n_mixes * self.desc_size * self.n_authorities
        c_bw += self.sig_size * self.n_authorities
        c_bw += self.n_clients * self.n_mixes * self.desc_size
        c_bw += self.n_clients * self.sig_size * self.n_authorities
        return c_bw / self.consensus_time

    @property
    def consensus_bandwidth_ratio(self):
        """ Returns the ratio of consensus bandwidth to network bandwidth as a whole """
        return self.consensus_bandwidth/self.network_bandwidth

    @property
    def consensus_overhead(self):
        """ Returns the bandwidth per client used for distributing the consensus in bits/second """
        return self.consensus_bandwidth_ratio *\
                (self.network_bandwidth / self.n_clients)

    @property
    def consensus_size(self):
        """ Returns the size, in bytes, of the consensus document """
        return self.n_mixes * self.desc_size + self.n_authorities * self.sig_size

    @property
    def network_bandwidth(self):
        """ Returns the network total bandwidth in bits/second """
        # consensus bandwidth in bit/s
        return self.consensus_bandwidth + self.client_average_bw * self.n_clients

    @property
    def mixes_required(self):
        """ Returns an approximate number of mixes needed """
        # XXX, approx - ignores consensus overhead
        return self.n_clients * self.client_average_bw / float(self.mix_bandwidth)

# Example
mix_params = MixParameters(
    # per mix bandwidth. assume mix can handle 1Gbps line rate at peak and want 50% load
    mix_bandwidth=5*10**8,
    consensus_time=60*60*3,
    n_authorities=9,
    lambda_p=10,
    message_size=51200,
    # XXX: desc_size: identity, link, and mix keys for 3 epochs,
    # 10 bytes of addresses (a guess), and 2 bytes from field
    desc_size=32+32+3*32+10+2,
    sig_size=64,
    )

# XXX pass by argument or config
for noise in [0, .5, 2, 9]: # noise / signal ratio of decoy traffic.
    mix_params.noise_signal = noise
    for n_client in [10**4, 10**5, 10**6, 10**8]: # number of clients
        mix_params.n_clients = n_client
        print mix_params
