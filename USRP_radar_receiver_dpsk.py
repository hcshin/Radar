#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Usrp Radar Receiver Proto Dpsk
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
from scipy import signal


def Find_Cor(Acode, Bcode):
    #derive maximum correlation value by the length of the second operand
    #N.B. this operation may not be commutative although cross-corrllation is commutative
    return numpy.divide( float(max(numpy.correlate(Acode,Bcode,'full'))) , len(Bcode) )


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
        self.file_sink = blocks.file_sink(gr.sizeof_char*1, "rcvd_code.byte", False)
        self.file_sink.set_unbuffered(False)

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
        self.byte_decimation = hocheol.byte_decim_bb()

        ##################################################
        # Connections
        ##################################################
        self.connect((self.dbpsk_demod, 0), (self.unpacked_to_packed, 0))
        self.connect((self.rational_resampler, 0), (self.dbpsk_demod, 0))
        self.connect((self.receiveUSRP, 0), (self.rational_resampler, 0))
        self.connect((self.unpacked_to_packed, 0), (self.byte_decimation, 0))
        self.connect((self.byte_decimation, 0), (self.file_sink, 0))



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
#    time.sleep(10)

    while 1:
        time.sleep(60) #To saturate buffer
        tb.stop()
        Rarr=[]
        #byte to python variable (1, -1, or 0)
        with open('rcvd_code.byte', 'rb') as f:
            for chunk in iter(lambda: f.read(1), b''):
                if chunk.encode('hex') == 'ff' :
                    Rarr.append(-1)
    			
                elif chunk.encode('hex') == '01' :
          	    Rarr.append(1)
    	        else:
	            Rarr.append(0)
        print('Received buffer length = %d' % len(Rarr))

        tb.file_sink.close() #reset file buffer
        tb.file_sink.open("rcvd_code.byte")
        tb.wait() #Wait till the reconfiguration completes
        tb.start() #Restart flowgraph

        spoint = 0 #Start point
        fpoint = 0 #End point
        Carray = pickle.load(open('codes_passed_PSLR_dB_and_PCR_criterion.pickle')) #Load code set

        while 1: #Infinitely brute-force incoming radar pulses
            pspoint=spoint
            #Search for the start point
            #Start point == first nonzero element
            for x in range(spoint,len(Rarr)-1):
                if Rarr[x] != 0 :
                    spoint=x
                    break
            #Search for the end point
            #End point == the position followed by 20 consecutive zeros
            #I know the following routine is very inefficient... (note for future optimization)
            for x in range(spoint,len(Rarr)-1):
                a=0
                for y in range(19):
                    #x == start index of the search window
                    #y == relative search index from x (increses by 1 for every loops)
                    #x+y == absolute search index (from index 0. Also increses)
                    #min(x+y,len(Rarr)-1): minimum index between the end of buffer and current absolute index
                    #^to prevent out-of-bound error
                    a=a+abs(Rarr[min(x+y,len(Rarr)-1)]) #if 0 continues to appear the value of a will remain 0
                    #if there are consecutive 20 zeros
                    if a == 0 :
                        fpoint = x; #let the end index of the code to be the start index of the search window
                        break

            Rcode = Rarr[spoint:fpoint-1] #extract received code chunk
            print 'code chunk start & end index\n\t=(%d, %d)' % (spoint, fpoint)
            if spoint == fpoint:
                break

            #ignore codes whose length is below 13 (to filter out apparent false-positives)
            if fpoint - spoint < 13:
                spoint = fpoint
                break
            spoint=fpoint #restart search from the end point of the code chunk (this is also inefficient)

            maxCor=0.0 #To store the maximum cross-correlation value
            maxIndex=0 #To store the code index of the  maximum cross-correlation value
            print('candidate code list which exceeds the threshold --------------------')
            for x in range(len(Carray)):
                code = Carray[x][0] #extract code (N.B. Carry structure: [[code], PCR, PSLR_dB])
                tmpCor = Find_Cor(code, Rcode)
                tmpCor2 = Find_Cor(Rcode, code) #reverse correlation

                if tmpCor2 >= 0.8 or tmpCor >= 0.9:
                    print('(code index, code length, cross-corr, cross-corr-rev)\n\t=(%d, %d, %f, %f)' % (x, len(code), tmpCor, tmpCor2))

                #refresh maximum correlation value
                if maxCor < tmpCor:
                    maxIndex = x
                    maxCor = tmpCor

            print('Max-------------------------------')
            print('Maximum cross-corralation = %f' % maxCor)
            print('Index of the code = %d' % maxIndex)
            print('----------------------------------\n\n') 
        # while loop for Identifying end			
    #while loop for tb end
    raw_input('Press Enter to quit: ')
    tb.stop()
    tb.wait()
