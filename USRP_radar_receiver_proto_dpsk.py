#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Dpsk Test Usrp
# Generated: Mon Jan 19 17:20:05 2015
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
import pickle
import numpy
import time
import pickle
import numpy
from scipy import signal


def Find_Cor(Acode, Bcode):
    return numpy.divide( float(max(numpy.correlate(Acode,Bcode,'full'))) , len(Bcode) )


class dpsk_test_USRP(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Dpsk Test Usrp")

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
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, "rcvd_code.byte", False)
        self.blocks_file_sink_0.set_unbuffered(False)

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
#        self.char_to_float = blocks.char_to_float(1, 1)
        self.byte_decimation = hocheol.byte_decim_bb()

        ##################################################
        # Connections
        ##################################################
        self.connect((self.dbpsk_demod, 0), (self.unpacked_to_packed, 0))
        self.connect((self.rational_resampler, 0), (self.dbpsk_demod, 0))
        self.connect((self.receiveUSRP, 0), (self.rational_resampler, 0))
        self.connect((self.unpacked_to_packed, 0), (self.byte_decimation, 0))
        self.connect((self.byte_decimation, 0), (self.blocks_file_sink_0, 0))



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
    tb = dpsk_test_USRP()
    tb.start()
#    time.sleep(10)

    while 1:
        time.sleep(60)
        tb.stop()
        Rarr=[]
        with open('rcvd_code.byte', 'rb') as f:
            for chunk in iter(lambda: f.read(1), b''):
                if chunk.encode('hex') == 'ff' :
                    Rarr.append(-1)
    			
                elif chunk.encode('hex') == '01' :
          	    Rarr.append(1)
    	        else:
	            Rarr.append(0)
	    print len(Rarr)

        tb.blocks_file_sink_0.close()
        tb.blocks_file_sink_0.open("rcvd_code.byte")
        tb.wait()
        tb.start()

        spoint = 0
        fpoint = 0
        Carray = pickle.load(open('codes_passed_PSLR_dB_and_PCR_criterion.pickle'))

        while 1:
            pspoint=spoint
    	    for x in range(spoint,len(Rarr)-1):
	        if Rarr[x] != 0 :
		    spoint=x
		    break
	    for x in range(spoint,len(Rarr)-1):
	        a=0
	        for y in range(0,19):
		    a=a+abs(Rarr[min(x+y,len(Rarr)-1)])
	        if a == 0 :
		    fpoint = x;
		    break
		
    	    Rcode = Rarr[spoint:fpoint-1]
	    print(spoint, fpoint)
	    if spoint == fpoint:
	        break

	    if fpoint - spoint < 13:
	        spoint = fpoint
	        break
	    spoint=fpoint
		

		
	    maxCor=0.0
	    maxIndex=0
	    print('candidate--------------------------')
	    for x in range(0,957):
	        code = Carray[x][0] 
	        tmpCor = Find_Cor(code, Rcode)
	        tmpCor2 = Find_Cor(Rcode, code)

                if tmpCor2 >= 0.8 or tmpCor >=0.9:
       	            print(x, len(code), tmpCor, tmpCor2  )
			
                if maxCor < tmpCor:
    	            maxIndex = x
		    maxCor = tmpCor
		    
            print('Max-------------------------------')
	    	    #    print(Carray[maxIndex][0])
            print(maxCor)
            print(maxIndex) 
            print('----------------------------------\n\n') 
        # while loop for Identifying end			
    #while loop for tb end




    raw_input('Press Enter to quit: ')




    tb.stop()
    tb.wait()
