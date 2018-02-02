#!/usr/bin/env python
s = 1
gigabit = 10**9
rtt = .3 * s
payload = 512 # in bytes
nsr = 2
mbr = .5 * gigabit * s # in bits/second
# find scaling parameter k
# nsr is noise/signal ratio of cover traffic
# rtt is average round-trip-time parameter
# mbr is average mix bandwidth rate
#  TODO: consider factors such as overprovisioning, peak demand, ddos
def scaling_k(noise_signal, message_size, rtt, mix_avg_bandwidth):
    byte = 8
    return (((1+noise_signal)*message_size*byte)/rtt)/(mix_avg_bandwidth)

def consensus_size(num_mixes, num_authorities, size_mix_descriptor, size_signature):
    return num_mixes * size_mix_descriptor + num_authorities * size_signature

def consensus_bandwidth(num_clients, num_mixes, size_mix_descriptor, num_authorities, size_signature, consensus_interval):
    b = 2 * num_mixes * size_mix_descriptor * num_authorities
    b += size_signature * num_authorities
    b += num_clients * num_mixes * size_mix_descriptor
    b += num_clients * size_signature * num_authorities
    return b / consensus_interval

def k_consensus_bandwidth(num_clients, k, size_mix_descriptor, num_authorities, num_mixes, size_signature, consensus_interval):
    b = 2 * num_clients * k * size_mix_descriptor * num_authorities
    b += size_signature * num_authorities
    b += num_clients * k * num_clients * size_mix_descriptor
    b += num_clients * size_signature * num_authorities
    return b / consensus_interval

# bandwidth channel
def bwc(message_size, rtt):
    return payload / rtt

# average bandwidth of all clients
def cbr(message_size, message_frequency, num_clients, noise_signal):
    return (1 + noise_signal) * bwc(message_size, message_frequency) * num_clients

# network bandwidth cumulative
def nbr(num_clients, num_mixes, num_authorities, size_mix_descriptor, size_signature, consensus_interval, message_size,
        message_frequency, noise_signal): 
    # consensus bandwidth
    cbw = consensus_bandwidth(num_clients, num_mixes, size_mix_descriptor, num_authorities, size_signature, consensus_interval)
    # client bandwidth
    cbr = cbr(message_size, message_frequency, num_clients, noise_signal)
    return cbw + cbr

# ratio of network bandwidth to consensus bandwidth
def rnbw(num_clients, num_mixes, num_authorities, size_mix_descriptor, size_signature, consensus_interval, message_size,
        message_frequency, noise_signal): 
    # consensus bandwidth
    cbw = consensus_bandwidth(num_clients, num_mixes, size_mix_descriptor, num_authorities, size_signature, consensus_interval)
    # client bandwidth
    return (cbr(message_size, message_frequency, num_clients, noise_signal) / cbw) / (1+noise_signal)

# number of mixes required 
def nmbr(message_size, message_frequency, num_clients, noise_signal, mix_avg_bandwidth):
    k = scaling_k(noise_signal, message_size, message_frequency, mix_avg_bandwidth)
    clients_per_mix = 1/k
    return num_clients / clients_per_mix

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
  #  // try nsr -> idgaf, 2, 9, 99

#Interesting things to plot
# number of mix nodes for 1k, 10k, 100k, 1M, 10M 100M, 1B clients:
# with low latency, short messages
# medium latency, short messages
# high latency, large messages

num_authorities = 5 # 
size_mix_descriptor = 100 # yolo
size_signature = 100
# Should produce a matrix...

# message_frequency should fit some kind of user experience/privacy expectation
mix_avg_bandwidth = .7 * 10**9 # 500 mbits @ 50% gig-e
for consensus_interval in [60, 600, 60*60*3, 60*60*24]:
    for message_frequency in [.3]: #, 1, 5, 30, 60, 300, 600, 3600]: # seconds
        for message_size in [512]: #, 1024, 50*1024, 10**6, 10**7]:
            for noise_signal in [0, 2, 9, 99]:
                for num_clients in [10**3,10**4,10**5, 10**6, 10**7, 10**8, 10**9]:
                    num_mixes = nmbr(message_size, message_frequency, num_clients,
                            noise_signal, mix_avg_bandwidth)
    
                    network_bandwidth_ratio = rnbw(num_clients, num_mixes, num_authorities,
                            size_mix_descriptor, size_signature,
                            consensus_interval, message_size, message_frequency,
                            noise_signal)
                    print "consensus_interval: {} n_clients: {}, n_mixes: {}, bw_ratio: {}, noise: {}".format(consensus_interval, num_clients, num_mixes, network_bandwidth_ratio, noise_signal)
# amount of bw used for consensus vs network bandwidth

