#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Usrp Radar Transmitter Proto
# Generated: Wed Dec 31 17:47:49 2014
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import filter
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from optparse import OptionParser
from datetime import datetime
import math
import time
import pickle
import random

class USRP_radar_transmitter_proto(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Usrp Radar Transmitter Proto")

        ##################################################
        # Variables
        ##################################################
        self.sampRepeat = sampRepeat = 50
        self.transmitSampRate = transmitSampRate = 100e3
        self.rfFreq = rfFreq = 5e9
        self.USRPSampRate = USRPSampRate = transmitSampRate*100

        ##################################################
        # Blocks
        ##################################################
        self.transmitUSRP = uhd.usrp_sink(
        	",".join(("addr=192.168.10.2", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.transmitUSRP.set_samp_rate(USRPSampRate)
        self.transmitUSRP.set_center_freq(rfFreq, 0)
        self.transmitUSRP.set_gain(0, 0)
        self.transmitUSRP.set_antenna("TX/RX", 0)
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=10,
                decimation=1,
                taps=None,
                fractional_bw=None,
        )
        self.dbpsk_mod = digital.dbpsk_mod(
        	samples_per_symbol=10,
        	excess_bw=0.35,
        	mod_code="gray",
        	verbose=False,
        	log=False)
        self.transmitBarkerCode = blocks.vector_source_b((0, 0, 0), True, 1, [])
        self.unpacked_to_packed = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
        self.streamMuxTransmitPulse = blocks.stream_mux(gr.sizeof_char*1, (1, 1))
        self.codeRepeat = blocks.repeat(gr.sizeof_char*1, sampRepeat)
        self.float_to_char = blocks.float_to_char(1, 1)
        self.char_to_float_0 = blocks.char_to_float(1, 10)
        self.const_source = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 17)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.transmitBarkerCode, 0), (self.codeRepeat, 0))
        self.connect((self.const_source, 0), (self.float_to_char, 0))
        
        self.connect((self.codeRepeat, 0), (self.streamMuxTransmitPulse, 0))
        self.connect((self.float_to_char, 0), (self.streamMuxTransmitPulse, 1))
        self.connect((self.streamMuxTransmitPulse, 0), (self.dbpsk_mod, 0))
        self.connect((self.dbpsk_mod, 0), (self.rational_resampler, 0))
        self.connect((self.rational_resampler, 0), (self.transmitUSRP, 0))


    def get_transmitSampRate(self):
        return self.transmitSampRate

    def set_transmitSampRate(self, transmitSampRate):
        self.transmitSampRate = transmitSampRate
        self.pulseBaseCarrier.set_sampling_freq(self.transmitSampRate)
        self.trasmitUSRP.set_samp_rate(self.transmitSampRate)

    def get_rfFreq(self):
        return self.rfFreq

    def set_rfFreq(self, rfFreq):
        self.rfFreq = rfFreq
        self.trasmitUSRP.set_center_freq(self.rfFreq, 0)

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option('-i', '--infile_name', dest='dir_candidate_codes', help='List of compound Barker codes to transmit pulses', metavar='input_file_dest', default='codes_passed_PSLR_dB_and_PCR_criterion.pickle')
    parser.add_option('-r', '--pulse_ratio', dest='pulse_ratio', help='Ratio of pulse to null signal lengths', metavar='pulse_ratio', default=5)
    (options, args) = parser.parse_args()
    dir_candidate_codes = options.dir_candidate_codes
    pulse_ratio = int(options.pulse_ratio)

    #import candidate Barker codes
    input_file_pt = open(dir_candidate_codes, 'rb')
    candidate_codes = pickle.load(input_file_pt)
    input_file_pt.close()

    #randomly choose one of candidate Barker codes
    proto = USRP_radar_transmitter_proto()
    proto.transmitCodeWrapper = candidate_codes[random.randrange(len(candidate_codes))]
    #transmitCodeWrapper structure
    #[[code], PSLR_dB, PCR]
    proto.transmitCode = proto.transmitCodeWrapper[0]
    #map 1 to 255, -1 to 0
    proto.mapping = {-1:255, 1:0}
    proto.transmitCode = [proto.mapping[chip] for chip in proto.transmitCode]
    #derive code length
    proto.transmitCodeLen = len(proto.transmitCode)
    #(Optional) pickle transmitCode
    current = str(datetime.now()) #save current time
    current_date = current.split()[0] #extract year-month-date info
    current_time = current.split()[1].split('.')[0] #extract hr:min:sec info
    code_pickle_pt = open('transmitCode_' + current_date + '_' + current_time + '.pickle', 'wb')
    pickle.dump(proto.transmitCode, code_pickle_pt)
    code_pickle_pt.close()

    #assign transmitCode to vector source
    proto.transmitBarkerCode.set_data(proto.transmitCode)
    #modify stream mux & repeat block parameters 
    #disconnect, delete, re-instantiate, and re-connect stream mux
    ##disconnect
    proto.disconnect((proto.codeRepeat, 0), (proto.streamMuxTransmitPulse, 0))
    proto.disconnect((proto.float_to_char, 0), (proto.streamMuxTransmitPulse, 1))
    proto.disconnect((proto.streamMuxTransmitPulse, 0), (proto.dbpsk_mod, 0))
    ##delete & re-instantiate
    proto.streamMuxTransmitPulse.__del__()
    proto.streamMuxTransmitPulse = blocks.stream_mux(gr.sizeof_char*1, (proto.transmitCodeLen*proto.sampRepeat, pulse_ratio*proto.transmitCodeLen*proto.sampRepeat))
    ##reconnect
    proto.connect((proto.codeRepeat, 0), (proto.streamMuxTransmitPulse, 0))
    proto.connect((proto.float_to_char, 0), (proto.streamMuxTransmitPulse, 1))
    proto.connect((proto.streamMuxTransmitPulse, 0), (proto.dbpsk_mod, 0))

    proto.start()
    raw_input('Press Enter to quit: ')
    proto.stop()
    proto.wait()
