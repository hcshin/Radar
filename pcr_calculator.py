from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import pickle
import random
import math
import threading
import pdb

class PCR_calculator(gr.top_block):
    
    def __init__(self, samp_rate, fft_size, repetition):
        gr.top_block.__init__(self, "PCR_calculator")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate
        self.repetition = repetition
        self.fft_size = fft_size
        
        ##################################################
        # Blocks
        ##################################################
        self.fft = fft.fft_vfc(fft_size, True, (window.hamming(fft_size)), 1)
        self.vector_source = blocks.vector_source_f((0, 0, 0), False, 1, [])
        self.vector_sink = blocks.vector_sink_f(fft_size)
        #self.file_sink = blocks.file_sink(gr.sizeof_float*fft_size, "spectrum_out.float", False)
        #self.file_sink.set_unbuffered(False)
        self.throttle_0 = blocks.throttle(gr.sizeof_float*1, samp_rate, True)
        self.throttle_1 = blocks.throttle(gr.sizeof_float*1, samp_rate, True)
        self.stream_to_vector = blocks.stream_to_vector(gr.sizeof_float*1, fft_size)
        self.repeat = blocks.repeat(gr.sizeof_float*1, repetition)
        self.multiply = blocks.multiply_vff(1)
        self.signal_source = analog.sig_source_f(samp_rate, analog.GR_COS_WAVE, 1000, 1, 0)
        self.complex_to_mag = blocks.complex_to_mag(fft_size)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.vector_source, 0), (self.throttle_0, 0), \
                (self.repeat, 0), (self.multiply, 0))
        self.connect((self.signal_source, 0), (self.throttle_1, 0), \
                (self.multiply, 1))
        #self.connect((self.multiply, 0), (self.stream_to_vector, 0), \
                #(self.fft, 0), (self.complex_to_mag, 0), (self.file_sink, 0))
        self.connect((self.multiply, 0), (self.stream_to_vector, 0), \
                (self.fft, 0), (self.complex_to_mag, 0), (self.vector_sink, 0))

#Class for multithreaded PCR calculation
class PCR_calculator_wrapper(threading.Thread):
    def __init__(self, threadID, candidate_codes_partition, fft_size, repetition, output_code_list):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.candidate_codes_partition = candidate_codes_partition
        self.fft_size = fft_size
        self.repetition = repetition
        self.output_code_list = output_code_list

    def run(self):
        print "Starting thread %d" % self.threadID

        #instantiate flowgraph
        self.flowgraph = PCR_calculator(samp_rate, self.fft_size, self.repetition)

        num_of_candidate_codes = len(self.candidate_codes_partition)
        for candidate_code_wrapper in self.candidate_codes_partition:
            #Structure of candidate_code_wrapper
            #[[compound Barker code itself], PSLR_dB]
            candidate_code = candidate_code_wrapper[0] #extract candidate code

            #set code and run till completion
            self.flowgraph.vector_source.set_data(list(candidate_code))
            self.flowgraph.start()
            self.flowgraph.wait()

            #calculate pulse_dur for each pulse
            #pulse_dur = [# of samples for pulse] / [samp_rate]
            pulse_dur = (len(candidate_code) * self.repetition) / samp_rate

            #get fft result
            fft_plot = self.flowgraph.vector_sink.data()
            self.flowgraph.vector_sink.reset()
            num_of_blocks = len(fft_plot) / self.fft_size
            pcr_list = []
            progress = 0
            for block_index in range(num_of_blocks):
                one_block = fft_plot[block_index * self.fft_size:(block_index+1) * self.fft_size - 1]
                half_block = one_block[0:self.fft_size/2 - 1] #Samples are all real: Only half a block is meaningful
                peak = max(half_block) #Peak value
                threedB_indices = [idx for idx in range(len(half_block)) if half_block[idx] >= peak / 2] #get indices exceeds 3dB point below the peak value
                #pulse_BW = ([largest(=last) index of threedB_indices] - [smallest(=first) index of threedB_indices]) * [BW for one freq bin interval(=samp_rate/self.fft_size)]
                pulse_BW = (threedB_indices[-1] - threedB_indices[0])*samp_rate/self.fft_size
                #record pcr's derived from one partial interval
                #PCR = pulse_BW * pulse_dur (B*tau)
                #Note that PCR is independent to samp_rate
                #Since, pulse_BW * pulse_dur
                #= ([# of bins in 3dB BW]*samp_rate/fft_size)*([# of samples in candidate_code]/samp_rate)
                #=[# of bins in 3dB BW]*[# of samples in candidate_code]/samp_rate
                pcr_list.append(pulse_BW * pulse_dur)
            
            #getting average as pcr value for the pulse
            pcr = sum(pcr_list) / float(len(pcr_list))
            if pcr >= min_PCR:
                #Note that list appending is atomic (no need for locking)
                #pdb.set_trace()
                candidate_code_wrapper.append(pcr)
                self.output_code_list.append(candidate_code_wrapper)
                threadLock.acquire() #Lock for print progress
                print 'len(output_code_list) = %d' % len(self.output_code_list)
                threadLock.release() #Release lock

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option('-i', '--input_dest', dest='dir_candidate_codes', help='List of compound Barker codes which passed PSLR_dB criterion', metavar='input_file_dest', default='codes_passed_PSLR_dB_criterion.pickle')
    parser.add_option('-o', '--output_dest', dest='dir_output_dest', help='List of compound Barker codes which passed PSLR_dB & PCR criterion', metavar='output_file_dest', default='codes_passed_PSLR_dB_and_PCR_criterion.pickle')
    (options, args) = parser.parse_args()
    dir_candidate_codes = options.dir_candidate_codes
    dir_output_dest = options.dir_output_dest

    #Common parameters
    fft_size = 128
    samp_rate = 2e6
    repetition = 10
    min_PCR = 500

    input_file_pt = open(dir_candidate_codes, 'rb')
    candidate_codes = pickle.load(input_file_pt)
    input_file_pt.close()
    #scramble the list order for multithreading
    random.shuffle(candidate_codes)

    output_code_list = []
    num_of_candidate_codes = len(candidate_codes)
    print 'num_of_candidate_codes', num_of_candidate_codes

    #partition for multithreading
    num_of_threads = 10
    num_of_ele_per_thread = num_of_candidate_codes / num_of_threads
    PCR_calculators = [] #List container for threads
    threadLock = threading.Lock()
    #instantiate threads and start them
    for n in range(num_of_threads - 1):
        PCR_calculators.append(PCR_calculator_wrapper(n, candidate_codes[num_of_ele_per_thread*n:num_of_ele_per_thread*(n+1)], fft_size, repetition, output_code_list))
        candidate_codes[num_of_ele_per_thread*n:num_of_ele_per_thread*(n+1)] = []
        #pdb.set_trace() #For debug
        PCR_calculators[n].start()
    #instantiate and start the last thread
    n += 1
    PCR_calculators.append(PCR_calculator_wrapper(n, candidate_codes, fft_size, repetition, output_code_list))
    del candidate_codes
    PCR_calculators[n].start()

    #Wait for threads to be terminated
    for t in PCR_calculators:
        t.join()

    print "All threads are terminated"
    pickle.dump(output_code_list, open(dir_output_dest, 'wb'))
