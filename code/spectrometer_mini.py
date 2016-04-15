#!/usr/bin/env python
'''
This script configuring the wideband spectrometer and plotting the received data using the Python KATCP library along with the katcp_wrapper distributed in the corr package. 
Designed for use with MINI Telescope and ROACH platforms.\n

You need to have KATCP and CORR installed. Get them from http://pypi.python.org/pypi/katcp and http://casper.berkeley.edu/svn/trunk/projects/packetized_correlator/corr-0.4.0/

To run this script:
./spec12_32b_2bram.py 192.168.1.11 -g 262143 -l 65536
./spec12_32b_2bram.py 192.168.1.11 -g 262143 -l 65536 -b minispec_chopper_2016_Apr_12_1723.bof
minispec_chopper_2016_Apr_11_1331.bof
/home/roach/Desktop/roberto/mini_chopper/minispec_chopper/bit_files/
./spec12_32b_2bram.py 192.168.1.11 -g 262143 -l 1 -b minispec_chopper_2016_Apr_13_1742.bof

Gain = 2^18 - 1 = 262143 
accumulation length = 1 o 0 mode.
cal: 1
splobs: 0

\nAuthor: Andres, May 2015.
'''


import corr, time, numpy, struct, sys, logging, math, Gnuplot, Gnuplot.funcutils, array
from math import *


# bitstream = 'mini_spec_1ghz_1bram_2015_Sep_03_1058.bof'
#bitstream = 'minispec_1ghz_1bram_u_2015_Sep_04_1658.bof'
#bitstream = 'minispec_1ghz_1bram_u_2015_Sep_04_1939.bof'
bitstream = 'robtest.bof'



katcp_port=7147

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def get_data():
    #get the data...    
    acc_n = fpga.read_uint('acc_cnt')
    
    bla = fpga.read_uint('gpio_state')
    print bla
    #fpga.write_int('data_ctrl_lec_done',0)
    #fpga.write_int('data_ctrl_sel_we',1)

    a_0l=struct.unpack('>2048I',fpga.read('bram0',2048*4,0))
#    a_1l=struct.unpack('>512I',fpga.read('dout0_1',512*4,0))
#    a_2l=struct.unpack('>512I',fpga.read('dout0_2',512*4,0))
#    a_3l=struct.unpack('>512I',fpga.read('dout0_3',512*4,0))
#
    a_0m=struct.unpack('>2048I',fpga.read('bram1',2048*4,0))
#    a_1m=struct.unpack('>512I',fpga.read('dout1_1',512*4,0))
#    a_2m=struct.unpack('>512I',fpga.read('dout1_2',512*4,0))
#    a_3m=struct.unpack('>512I',fpga.read('dout1_3',512*4,0))

    #fpga.write_int('data_ctrl_lec_done',1)
    #fpga.write_int('data_ctrl_sel_we',0)



    interleave_a=[]
    interleave_b=[]
    interleave_log=[]        
    interleave_log_b=[]

    for i in range(2048):
        interleave_a.append(float(float(a_0l[i])+1))#24 es el original
        #interleave_a.append(float(float(a_1l[i])+1))#24 es el original
        #interleave_a.append(float(float(a_2l[i])+1))#24 es el original
        #interleave_a.append(float(float(a_3l[i])+1))#24 es el original
        interleave_b.append(float(float(a_0m[i])+1))
        #interleave_b.append(float(float(a_1m[i])+1))
        #interleave_b.append(float(float(a_2m[i])+1))
        #interleave_b.append(float(float(a_3m[i])+1))

    for k in range(4*512):
        interleave_log.append(10*log10(interleave_a[k]))
        interleave_log_b.append(10*log10(interleave_b[k]))

    return acc_n, interleave_a, interleave_log, interleave_log_b

def continuous_plot(fpga):
    ok=1
    bw=trunc(fpga.est_brd_clk())*4
    acc_n, interleave_a, interleave_log, interleave_log_b = get_data()
    g0.clear()    
    g0.title('ADC0 acc:'+str(acc_n)+' | Bw= '+str(bw)+' MHz ')
    g0.ylabel('Power AU (dB)')
    g0('set style data linespoints')
    g0('set yrange [0:100]')
    g0('set xrange [-50:2098]')
    g0('set ytics 5')
    g0('set xtics 256')
    g0('set grid y')
    g0('set grid x')

    g1.clear()
    g1.title('ADC1 acc:'+str(acc_n)+' | Bw= '+str(bw)+' MHz ')
    g1.ylabel('Power AU (dB)')
    g1('set style data linespoints')
    g1('set yrange [0:100]')
    g1('set xrange [-50:2098]')
    g1('set ytics 5')
    g1('set xtics 256')
    g1('set grid y')
    g1('set grid x')

    while ok==1 :
        acc_n, interleave_a, interleave_log, interleave_log_b = get_data()
        #analog_freq = linspace(0, bw, spec_len)
        g0.plot(interleave_log)
        g0.title('ADC0 acc:'+str(acc_n)+' | Bw= '+str(bw)+' MHz')
        time.sleep(0.2)
        # print 'bram0 = ',interleave_a # print a_0l
        time.sleep(0.2)
        g1.plot(interleave_log_b)
        g1.title('ADC1 acc:'+str(acc_n)+' | Bw= '+str(bw)+' MHz')





################   START OF MAIN   ################

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=1,
        help='defaults values: 1 for cal and 0 for splobs.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0x00001000,
        help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-o', '--splobs', dest='splobs', type='int',default=11719,
        help='Set the Spectral Line Observation length. Default is 11719 (max).')
    p.add_option('-c', '--cal', dest='cal', type='int',default=7280,
        help='Set the Calibration length. Default is 7280 (max).')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile',type='str', default='robtest.bof',
        help='Specify the bof file to load')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. Run with the -h flag to see all options.\nExiting.'
        exit()
    else:
        roach = args[0] 
    if opts.boffile != '':
        bitstream = opts.boffile

try:
    loggers = []
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s on port %i... '%(roach,katcp_port)),
    fpga = corr.katcp_wrapper.FpgaClient(roach, katcp_port, timeout=10,logger=logger)
    time.sleep(1)

    if fpga.is_connected():
        print 'ok\n'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print '------------------------'
    print 'Programming FPGA with %s...' %bitstream,
    if not opts.skip:
        fpga.progdev(bitstream)
        print 'done'
    else:
        print 'Skipped.'
#
    print 'waiting 3 seconds...'
    time.sleep(3)
#
    print 'Configuring FFT shift register...',
    fpga.write('shift_ctrl','\x00\x00\x0f\xff')
    print 'done'
#
    print 'Configuring accumulation period...',
    fpga.write_int('acc_len',opts.acc_len)
    print 'done'
#
    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'

    print 'Configuring SPLOBS register...',
    fpga.write_int('splobs',opts.splobs)  
    print 'done'

    print 'Configuring CAL register...',
    fpga.write_int('cal',opts.cal)
    print 'done'
#
    print 'Setting digital gain of all channels to %i...'%opts.gain,
    if not opts.skip:
        fpga.write_int('gain',opts.gain) #write the same gain for all inputs, all channels
        print 'done'
    else:   
        print 'Skipped.'
    
    #set up the figure with a subplot to be plotted
    g0 = Gnuplot.Gnuplot(debug=0)
    g1 = Gnuplot.Gnuplot(debug=0)

    continuous_plot(fpga)	

    print 'Plot started.'

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

