#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Usrp Radar Receiver Proto Dpsk
# Generated: Mon Jan 19 17:24:31 2015
##################################################

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import hocheol
import time

class USRP_radar_receiver_proto_dpsk(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Usrp Radar Receiver Proto Dpsk")

        ##################################################
        # Variables
        ##################################################
        self.base_samp_rate = base_samp_rate = 100e3
        self.rfFreq = rfFreq = 5e9
        self.USRPSampRate = USRPSampRate = base_samp_rate*100

        ##################################################
        # Blocks
        ##################################################
        self.unpacked_to_packed = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
        self.receiveUSRP = uhd.usrp_source(
        	",".join(("addr=192.168.30.2", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.receiveUSRP.set_samp_rate(USRPSampRate)
        self.receiveUSRP.set_center_freq(rfFreq, 0)
        self.receiveUSRP.set_gain(0, 0)
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=1,
                decimation=10,
                taps=None,
                fractional_bw=None,
        )
        self.null_sink_start_here = blocks.null_sink(gr.sizeof_float*1)
        self.dbpsk_demod = digital.dbpsk_demod(
        	samples_per_symbol=10,
        	excess_bw=0.35,
        	freq_bw=6.28/100.0,
        	phase_bw=6.28/100.0,
        	timing_bw=6.28/100.0,
        	mod_code="gray",
        	verbose=False,
        	log=False
        )
        self.char_to_float = blocks.char_to_float(1, 1)
        self.byte_decimation = hocheol.byte_decim_bb()

        ##################################################
        # Connections
        ##################################################
        self.connect((self.dbpsk_demod, 0), (self.unpacked_to_packed, 0))
        self.connect((self.rational_resampler, 0), (self.dbpsk_demod, 0))
        self.connect((self.receiveUSRP, 0), (self.rational_resampler, 0))
        self.connect((self.unpacked_to_packed, 0), (self.byte_decimation, 0))
        self.connect((self.byte_decimation, 0), (self.char_to_float, 0))
        self.connect((self.char_to_float, 0), (self.null_sink_start_here, 0))



    def get_base_samp_rate(self):
        return self.base_samp_rate

    def set_base_samp_rate(self, base_samp_rate):
        self.base_samp_rate = base_samp_rate
        self.set_USRPSampRate(self.base_samp_rate*100)

    def get_rfFreq(self):
        return self.rfFreq

    def set_rfFreq(self, rfFreq):
        self.rfFreq = rfFreq
        self.receiveUSRP.set_center_freq(self.rfFreq, 0)

    def get_USRPSampRate(self):
        return self.USRPSampRate

    def set_USRPSampRate(self, USRPSampRate):
        self.USRPSampRate = USRPSampRate
        self.receiveUSRP.set_samp_rate(self.USRPSampRate)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = USRP_radar_receiver_proto_dpsk()
    tb.start()
    raw_input('Press Enter to quit: ')
    tb.stop()
    tb.wait()
