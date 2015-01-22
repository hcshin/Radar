#! /usr/bin/env python
from optparse import OptionParser
from gnuradio.eng_option import eng_option
from copy import copy
import numpy
import itertools
import math
import pickle

#ingredients
basic_barker = ((1, -1), \
        (1, 1), \
        (1, 1, -1), \
        (1, 1, -1, 1), \
        (1, 1, 1, -1), \
        (1, 1, 1, -1, 1), \
        (1, 1, 1, -1, -1, 1, -1), \
        (1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1), \
        (1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1))

def combine(to_be_put, into, index):
    to_be_put = list(to_be_put)
    into = list(into)

    into[index:index] = (into.pop(index)*numpy.array(to_be_put)).tolist()
    return into

def compound(inner_code, outer_code):
    inner_code = list(inner_code)
    outer_code = list(outer_code)
    #Derives Kroneker product
    compound_result = []
    for i in outer_code:
        compound_result.extend((i*numpy.array(inner_code)).tolist())
    return compound_result

def serialCompound(index_series):
    serial_compound_result = [1]
    for index in index_series:
        serial_compound_result = compound(serial_compound_result, basic_barker[index])
    return serial_compound_result

def limitedPrimeFacto(num):
    #Prime Factorization for numbes whose prime factor do not exceed 13. Repetition is allowed. Prime factors are in ascending order.
    prime_fac = []
    divisor = 2
    while divisor**2 <= num and divisor <= 13:
        while num % divisor == 0:
            prime_fac.append(divisor)
            num /= divisor
        divisor += 1
    if num > 13:
        return False
    elif num > 1:
        prime_fac.append(num)
        return prime_fac
    else:
        return prime_fac

def getLimitedPrimeFactoList(lower, upper):
    prime_fac_list = [] #Enumerator for the result
    for each_num in range(lower, upper+1):
        limited_prime_fact = limitedPrimeFacto(each_num)
        if limited_prime_fact: #If each_num is limited prime factorizable
            prime_fac_list.append(limited_prime_fact)
    return prime_fac_list


def groupBy2(prime_fac_list):
    group_by_2 = []
    for prime_fac in prime_fac_list:
        count2 = prime_fac.count(2)
        if count2 > 1: #In case of more than two 2's
            #Remove 2's from the list
            prime_fac = filter(lambda x: x!=2, prime_fac)
            #Maximum possible number of 4's
            count4 = count2 / 2
            for num_of_4s in range(count4 + 1):
                group_by_2_ele = [] #list for enumeration
                #Add 2's
                group_by_2_ele.extend([2]*(count2 - 2*num_of_4s))
                #Add 4's
                group_by_2_ele.extend([4]*num_of_4s)
                #Add remainings
                group_by_2_ele.extend(prime_fac)
                #Add group_by_2_ele to group_by_2
                group_by_2.append(group_by_2_ele)
        else: #If there is no more than one 2's
            group_by_2.append(prime_fac)

    return group_by_2

def assignCase24AndIndices(group_by_2):
    case24_and_index_assign_result = []
    #Index for 2A = 0, 2B = 1
    possibility_set2 = [0, 1]
    #Index for 4A = 3, 4B = 4
    possibility_set4 = [3, 4]
    index_mapping_dict = {3:2, 5:5, 7:6, 11:7, 13:8}
    for group_by_2_ele in group_by_2:
        count2 = group_by_2_ele.count(2)
        count4 = group_by_2_ele.count(4)
        group_by_2_ele = filter(lambda x: x!=2 and x!=4, group_by_2_ele)
        for permute2_with_reps in itertools.combinations_with_replacement(possibility_set2, count2): #Get all possible combinations with replacement for length 2
            for permute4_with_reps in itertools.combinations_with_replacement(possibility_set4, count4): #Get all possible combinations with replacement for length 4
                case24_and_index_assign_result_ele = []
                #Add each of all possible permutations to list element
                case24_and_index_assign_result_ele.extend(permute2_with_reps)
                case24_and_index_assign_result_ele.extend(permute4_with_reps)
                #Add remainings to list element by mapping each to its index
                case24_and_index_assign_result_ele.extend([index_mapping_dict[group_by_2_ele_ele] for group_by_2_ele_ele in group_by_2_ele])
                #Add case24_and_index_assign_result_ele to case24_and_index_assign_result
                case24_and_index_assign_result.append(case24_and_index_assign_result_ele)

    return case24_and_index_assign_result

def next_permutation(seq, pred=cmp):
    #It seems that python has no inherit function for getting permutations of lists with repeated elements. It is possible to inefficiently get it by removing repeated elements of the result of the normal permutations.
    #Or it is possible to adopt custom-built functions. permutation_next is one of custom-built functions
    """Like C++ std::next_permutation() but implemented as
    generator. Yields copies of seq."""
    def reverse(seq, start, end):
        # seq = seq[:start] + reversed(seq[start:end]) + \
        #       seq[end:]
        end -= 1
        if end <= start:
            return
        while True:
            seq[start], seq[end] = seq[end], seq[start]
            if start == end or start+1 == end:
                return
            start += 1
            end -= 1
    if not seq:
        raise StopIteration
    try:
        seq[0]
    except TypeError:
        raise TypeError("seq must allow random access.")
    first = 0
    last = len(seq)
    seq = seq[:]
    # Yield input sequence as the STL version is often
    # used inside do {} while.
    yield seq
    if last == 1:
        raise StopIteration
    while True:
        next = last - 1
        while True:
            # Step 1.
            next1 = next
            next -= 1
            if pred(seq[next], seq[next1]) < 0:
                # Step 2.
                mid = last - 1
                while not (pred(seq[next], seq[mid]) < 0):
                    mid -= 1
                seq[next], seq[mid] = seq[mid], seq[next]
                # Step 3.
                reverse(seq, next1, last)
                # Change to yield references to get rid of
                # (at worst) |seq|! copy operations.
                yield seq[:]
                break
            if next == first:
                raise StopIteration
    raise StopIteration

def getAllPerms(case24_and_index_assign_result):
    #Derive list of all possible permutations of case24 and indices assigned list
    all_perms = []
    for case24_and_index_assign_result_ele in case24_and_index_assign_result:
        for all_perms_ele in next_permutation(case24_and_index_assign_result_ele):
            all_perms.append(copy(all_perms_ele)) #Copy is needed since the output of next_permutation show kindof entaglement (i.e. it does not seem to pass the value but  the address or the reference)
    return all_perms

def getSerialCompoundResults(all_perms):
    #Apply serial compound operation to each ele in all perms
    serial_compound_results = []
    for all_perms_ele in all_perms:
        serial_compound_results.append(serialCompound(all_perms_ele))
    return serial_compound_results

def calculateAndFilterPSLR(compound_code_list, maximum_PSLR_dB):
    #Give each compounded code its PSRL_dB values
    compound_code_list_with_PSLR_dB = []
    for compound_code_list_ele in compound_code_list:
        autocorrelation_abs= numpy.absolute(numpy.correlate(compound_code_list_ele, compound_code_list_ele, 'full')).tolist()
        peak_amp = max(autocorrelation_abs) #largest value in abs(autocorrelation)
        autocorrelation_abs.remove(peak_amp)
        largest_subpeak_amp = max(autocorrelation_abs) #second largest value in abs(autocorrelation)
        PSLR_dB = 20*math.log10(largest_subpeak_amp / float(peak_amp))
        #IF PSLR_dB is largher than maximum_PSLR_dB, filter out.
        if PSLR_dB > maximum_PSLR_dB:
            continue
        compound_code_list_with_PSLR_dB.append([compound_code_list_ele, PSLR_dB])
    return compound_code_list_with_PSLR_dB

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option('-o', '--outfile_name', dest='dir_output_dest', help='List of compound Barker codes with certain range of length', metavar='output_file_dest', default='codes_with_length_criterion.pickle')
    parser.add_option('-m', '--min_len', dest='min_code_len', help='Minimum compound Barker code length', metavar='min_code_len', default=14)
    parser.add_option('-M', '--max_len', dest='max_code_len', help='Maximum compound Barker code length', metavar='max_code_len', default=3000)
    parser.add_option('-p', '--max_PSRL_dB', dest='maximum_PSLR_dB', help='Maximum PSLR_dB value', metavar='maximum_PSLR_dB', default=-10)
    (options, args) = parser.parse_args()
    dir_output_dest = options.dir_output_dest
    min_code_len = int(options.min_code_len)
    max_code_len = int(options.max_code_len)
    maximum_PSLR_dB = float(options.maximum_PSLR_dB)

    #step1 - get prime factorization of "min_code_len <= length <= max_code_len" where "2 <= prime factor <= 13"
    step1 = getLimitedPrimeFactoList(min_code_len, max_code_len)
    print 'step1 completed'
    print 'len(limited lrime facto list) = ', len(step1)

    #step2 - group prime factorization into 2 & 4
    step2 = groupBy2(step1)
    del step1
    print 'step2 completed'
    print 'len(grouped by 2 list) = ', len(step2)

    #step3 - Assign indices to prime factors. Especially for case of 2 & 4 assign two different indices. Derive all possible combinations of indices.
    step3 = assignCase24AndIndices(step2)
    del step2
    print 'step3 completed'
    print 'len(case4 and index assigned list) = ', len(step3)

    #step4 - Derive all permutations of inidices.
    step4 = getAllPerms(step3)
    del step3
    print 'step4 completed'
    print 'len(all possible perms list) = ', len(step4)

    #step5 - Assign actual barker codes to permutations of indices.
    step5 = getSerialCompoundResults(step4)
    del step4
    print 'step5 completed'
    print 'len(all compound Barker codes %d~%d long) = ' % (min_code_len, max_code_len), len(step5)
    pickle.dump(step5, open(dir_output_dest, 'wb'))
    
    #step 6 - Calculate each codes' PSLR and filter out by preset threshold.
    step6 = calculateAndFilterPSLR(step5, maximum_PSLR_dB)
    #N.B.
    #step 6 takes so long time. paralelization is needed
    #Possible approach: partition for loop in step 6 into 4(= #(CPU)) and execute
    del step5
    print 'step6 completed'
    print 'len(codes which passed PSLR_dB criterion) = ', len(step6)
    pickle.dump(step6, open(dir_output_dest.split('.')[0] + '+PSLR_dB_criterion.pickle', 'wb'))
