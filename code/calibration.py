#!/usr/bin/env python
'''
para correr la calibracion:

./calibracion.py 192.168.1.11 -g 0x0080000 -b calibracion_mini_500Mhz.bof

\nAuthor: Andres Alvear, November 2015.
'''
import corr,time,numpy,struct,sys,logging,pylab,matplotlib,math,Gnuplot, Gnuplot.funcutils,array, telnetlib, valon_synth
from math import *


bitstream = 'No_bof_file_error'
katcp_port=7147

def creartxt():
    archi=open('datos.dat','w')
    archi.close()

def creartxt():
    archi_teo=open('datos_teo.dat','w')
    archi_teo.close()

archi=open('datos.dat','a')
archi_teo=open('datos_teo.dat','a')    

creartxt()

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

    fpga.write_int('data_ctrl_lec_done',0)
    fpga.write_int('data_ctrl_sel_we',1)   

    re_0i=struct.unpack('>512q',fpga.read('dout0_0',512*8,0))
    im_0i=struct.unpack('>512q',fpga.read('dout0_1',512*8,0))
    re_2i=struct.unpack('>512q',fpga.read('dout0_2',512*8,0))
    im_2i=struct.unpack('>512q',fpga.read('dout0_3',512*8,0))
#
    re_0q=struct.unpack('>512q',fpga.read('dout1_0',512*8,0))
    im_0q=struct.unpack('>512q',fpga.read('dout1_1',512*8,0))
    re_2q=struct.unpack('>512q',fpga.read('dout1_2',512*8,0))
    im_2q=struct.unpack('>512q',fpga.read('dout1_3',512*8,0))

    fpga.write_int('data_ctrl_lec_done',1)
    fpga.write_int('data_ctrl_sel_we',0)

    spec_i=[]
    spec_q=[]
    power_spec_i=[]
    power_spec_q=[]
    amp_dif=[]
    phase_dif=[]
    e=10**-10
#    
    for i in range(512):
        spec_i.append(float(re_0i[i])/(2**18))
        spec_i.append(float(im_0i[i])/(2**18))
        spec_i.append(float(re_2i[i])/(2**18))
        spec_i.append(float(im_2i[i])/(2**18))
        spec_q.append(float(re_0q[i])/(2**18))
        spec_q.append(float(im_0q[i])/(2**18))
        spec_q.append(float(re_2q[i])/(2**18))
        spec_q.append(float(im_2q[i])/(2**18))

    
    return spec_i, spec_q


def arcotan(im,re):
    tan=0
    if im>=0.0 and re>=0.0:
        if re==0:
	    re=10**-20
        tan=atan(im/re)
    if im>=0.0 and re<=0.0:
        if im==0:
	    im=10**-20        	
        tan=pi/2+atan(abs(re)/im)
    if im<=0.0 and re<=0.0:
        if re==0:
	    re=10**-20
        tan=pi+atan(abs(im)/abs(re))
    if im<=0.0 and re>=0.0:
        if im==0:
	    im=10**-20
        tan=(3*pi/2)+atan(re/abs(im))
    return tan

def trunca(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]


################   START OF MAIN   ################

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('spectrometer.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-l', '--acc_len', dest='acc_len', type='int',default=2*(2**28)/2048,
        help='Set the number of vectors to accumulate between dumps. default is 2*(2^28)/2048, or just under 2 seconds.')
    p.add_option('-g', '--gain', dest='gain', type='int',default=0x00001000,
        help='Set the digital gain (6bit quantisation scalar). Default is 0xffffffff (max), good for wideband noise. Set lower for CW tones.')
    p.add_option('-s', '--skip', dest='skip', action='store_true',
        help='Skip reprogramming the FPGA and configuring EQ.')
    p.add_option('-b', '--bof', dest='boffile',type='str', default='',
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
#    print 'waiting 10 seconds...'
#    time.sleep(10)
#
# Se inicializan graficos y sus parametros.

    g0 = Gnuplot.Gnuplot(debug=0)
    g1 = Gnuplot.Gnuplot(debug=0)

    bw=trunc(fpga.est_brd_clk())*4
    print ('Bw obtenido es: '+str(bw))
    lo=input('LO frequency MHZ?)')
    start=lo-bw
    stop=lo+bw

    g0.clear()    
    g0.title('Upper Side Band amplitude ratio '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    g0.xlabel('Channel #')
    g0.ylabel('Power AU (dB)')
    g0('set style data linespoints')
    g0('set yrange [0.9:1.2]')
    g0('set xrange [-5:1027]')
    g0('set ytics 0.1')
    g0('set xtics 256')
    g0('set grid y')
    g0('set grid x')	

    g1.clear()    
    #g1.title('ADC0 spectrum using '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    #g1('unset key')
    g1('set title "Probe phase Upper Side Band"')
    g1.xlabel('Channel #')
    g1.ylabel('Degrees')
    g1('set style data points')
    g1('set yrange [-180:180]')
    g1('set xrange [0:1027]')
    g1('set ytics 10')
    g1('set xtics 256')
    g1('set grid y')
    g1('set grid x')
    #g1('set key box')
    #g1('unset multiplot')


    print 'Configuring FFT shift register...',
    fpga.write('shift_ctrl','\x00\x00\x0f\xff')
    print 'done'
#
    print 'Resetting counters...',
    fpga.write_int('cnt_rst',1) 
    fpga.write_int('cnt_rst',0) 
    print 'done'
#
    ti=time.time()
    bw=trunc(fpga.est_brd_clk())*4
        #rys = telnetlib.Telnet("192.168.1.35",5025)
    #valon=valon_synth.Synthesizer('/dev/ttyUSB0')
    agi = telnetlib.Telnet("192.168.1.34",5023)
    agi.write("freq 2.0ghz\r\n")
    agi.write("power -18dbm\r\n")
    agi.write("output on\r\n")
    def beep():
        print "\a"
    #rf = []
    razon_amplitud_usb = []
    diferencia_fase_usb = []
    razon_amplitud_lsb = []
    diferencia_fase_lsb = []
    #rys.write("output off\r\n")
    #rys.write("freq "+str(float(lo)/1000)+"ghz\r\n")
    #rys.write("output on\r\n")
    #points=input('Number of points? : ') #Numero de puntos para mostrar SRR
    #for i in range(points):
    #    rf.append(start+((stop-start)*i/points))


    archi.write('Freq'.rjust(7)+' '+'#Canal'.rjust(10)+' '+'real i'.rjust(7)+' '+'imag i'.rjust(7)+' '+'real q'.rjust(7)+' '+'imag q'.rjust(7)+' '+'amp_i'.rjust(7)+' '+'amp_q'.rjust(7)+' '+'phase_i'.rjust(7)+' '+'phase_q'.rjust(7)+' '+'amp_rat'.rjust(7)+' '+'ang_dif'.rjust(7)+' '+'phi'.rjust(7)+' \n')
    ch=input('number of channels(2^?): ')
    teo_upper=[]

################################################### Upper Side Band ##########################################################################
    for i in range(1*1024/(2**ch),1023,1024/(2**ch)): #usb
                tu=time.time()
                if i/20==float(i)/20:
                    beep()
                    print(str((tu-ti)/60)+' minutos'+' '+str(float(i)*100.0/2044)+'%')
                    print('Freq'.rjust(6)+' '+'#Canal'.rjust(6)+' '+'real i'.rjust(7)+' '+'imag i'.rjust(7)+' '+'real q'.rjust(7)+' '+'imag q'.rjust(7)+' '+'amp_i'.rjust(7)+' '+'amp_q'.rjust(7)+' '+'phase_i'.rjust(7)+' '+'phase_q'.rjust(7)+' '+'amp_rat'.rjust(7)+' '+'ang_dif'.rjust(7)+' '+'phi'.rjust(7)+' \n')
                    print(str(lo+(2*i)*float(bw)/2048)+' '+repr(2*i).rjust(6)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7)+' \n')

        	#valon.set_frequency(valon_synth.SYNTH_A,(2*i)*float(bw)/2048,0.0026)
    	        agi.write("freq "+ str(lo+(2*i)*float(bw)/2048) +"mhz\r\n")
		time.sleep(0.1)
                spec_i, spec_q = get_data()
		amp_i=((spec_i[2*i])**2+(spec_i[2*i+1])**2)**0.5
		amp_q=((spec_q[2*i])**2+(spec_q[2*i+1])**2)**0.5
		angle_i=arcotan(spec_i[2*i+1],spec_i[2*i])*180/(pi) #en grados
		angle_q=arcotan(spec_q[2*i+1],spec_q[2*i])*180/(pi) #en grados
		phi=arcotan(spec_q[2*i]*spec_i[2*i+1]-spec_i[2*i]*spec_q[2*i+1],spec_i[2*i]*spec_q[2*i]+spec_i[2*i+1]*spec_q[2*i+1])*180/(pi)
		#phi=atan((spec_q[2*i]*spec_i[2*i+1]-spec_i[2*i]*spec_q[2*i+1])/(spec_i[2*i]*spec_q[2*i]+spec_i[2*i+1]*spec_q[2*i+1]))*180/(pi)
		#phi=atan((spec_q[2*i]*spec_i[2*i+1]-spec_i[2*i]*spec_q[2*i+1])/(spec_i[2*i]*spec_q[2*i]+spec_i[2*i+1]*spec_q[2*i+1]))*180/(pi)


		if amp_q==0 or amp_i==0 :
                    amp_ratio=0.555555555555555555555555#estos datos son erroneos. Por algun motivo amp_q=0. se reemplazan por 0.555... para que no se caiga el script.
                else: 
                    amp_ratio=amp_i/amp_q# x del paper
                    #print type(amp_ratio)
                    #time.sleep(0.1)
                    #hola = amp_ratio
                    #Gnuplot.Data(hola,title='p z0 c y')
                    #g0.plot(hola)
                    razon_amplitud_usb.append([i,amp_ratio])
                    g0.plot(razon_amplitud_usb)

		phase_dif=(angle_i-angle_q)
		diferencia_fase_usb.append([i,phase_dif])
		#time.sleep(3)
		#print str(phase_dif)
		#time.sleep(0.1)
		
		#hola = phase_dif
		#print  hola
		g1.plot(diferencia_fase_usb)
		
                if phase_dif<0:
                   phase_dif=360+phase_dif
                teo_upper.append([1/(amp_ratio),lo+(2*i)*float(bw)/2048])
		teo_upper.append([180-phase_dif,lo+(2*i)*float(bw)/2048])
                amp_i=trunca(amp_i,2)
                amp_q=trunca(amp_q,2)
                angle_i=trunca(angle_i,2)
                angle_q=trunca(angle_q,2)
  		amp_rat=trunca(amp_ratio,2)
		ang_dif=trunca(phase_dif,2) 
		phi=trunca(phi,2)
		#print(str(lo+(2*i)*float(bw)/2048))
		print(trunca(lo+(2*i)*float(bw)/2048,2).rjust(6)+' '+repr(2*i).rjust(10)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7))
		archi.write(trunca(lo+(2*i)*float(bw)/2048,2).rjust(6)+' '+repr(2*i).rjust(10)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7)+' \n')

    g2 = Gnuplot.Gnuplot(debug=0)
    g3 = Gnuplot.Gnuplot(debug=0)

    bw=trunc(fpga.est_brd_clk())*4
    print ('BW obtenido es: '+str(trunc(fpga.est_brd_clk())*4))


    g2.clear()    
    g2.title('Lower Side Band amplitude ratio '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    g2.xlabel('Channel #')
    g2.ylabel('Power AU (dB)')
    g2('set style data linespoints')
    g2('set yrange [0.9:1.2]')
    g2('set xrange [-5:1027]')
    g2('set ytics 0.1')
    g2('set xtics 256')
    g2('set grid y')
    g2('set grid x')	

    g3.clear()    
    #g1.title('ADC0 spectrum using '+bitstream+' | Max frequency = '+str(bw)+' MHz')
    #g1('unset key')
    g3('set title "Probe phase Lower Side Band"')
    g3.xlabel('Channel #')
    g3.ylabel('Degrees')
    g3('set style data points')
    g3('set yrange [-180:180]')
    g3('set xrange [0:1027]')
    g3('set ytics 10')
    g3('set xtics 256')
    g3('set grid y')
    g3('set grid x')
    #g1('set key box')
    #g1('unset multiplot')
################################################### Lower Side Band ##########################################################################
    archi.write('lower_sideband'+' \n')
    archi.write('Freq'.rjust(7)+' '+'#Canal'.rjust(10)+' '+'real i'.rjust(7)+' '+'imag i'.rjust(7)+' '+'real q'.rjust(7)+' '+'imag q'.rjust(7)+' '+'amp_i'.rjust(7)+' '+'amp_q'.rjust(7)+' '+'phase_i'.rjust(7)+' '+'phase_q'.rjust(7)+' '+'amp_rat'.rjust(7)+' '+'ang_dif'.rjust(7)+' '+'phi'.rjust(7)+' \n')      
    teo_lower=[]
    for i in range(1*1024/(2**ch),1023,1024/(2**ch)):#lsb
        	tl=time.time()
                if i/20==float(i)/20:
                    beep()
                    print(str((tu-ti)/60)+' minutos'+' '+str(float(i)*100.0/2044)+'%')
                    print('Freq'.rjust(6)+' '+'#Canal'.rjust(6)+' '+'real i'.rjust(7)+' '+'imag i'.rjust(7)+' '+'real q'.rjust(7)+' '+'imag q'.rjust(7)+' '+'amp_i'.rjust(7)+' '+'amp_q'.rjust(7)+' '+'phase_i'.rjust(7)+' '+'phase_q'.rjust(7)+' '+'amp_rat'.rjust(7)+' '+'ang_dif'.rjust(7)+' '+'phi'.rjust(7)+' \n')
                    print(str(lo-(2*i)*float(bw)/2048)+' '+repr(2*i).rjust(6)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7)+' \n')
        	#valon.set_frequency(valon_synth.SYNTH_A,(2*i)*float(bw)/2048,0.0026)
    	        agi.write("freq "+ str(lo-(2*i)*float(bw)/2048) +"mhz\r\n")
		time.sleep(0.1)
                spec_i, spec_q = get_data()
		amp_i=((spec_i[2*i])**2+(spec_i[2*i+1])**2)**0.5
		amp_q=((spec_q[2*i])**2+(spec_q[2*i+1])**2)**0.5
		angle_i=arcotan(spec_i[2*i+1],spec_i[2*i])*180/(pi) #en grados
		angle_q=arcotan(spec_q[2*i+1],spec_q[2*i])*180/(pi) #en grados
		phi=arcotan(spec_q[2*i]*spec_i[2*i+1]-spec_i[2*i]*spec_q[2*i+1],spec_i[2*i]*spec_q[2*i]+spec_i[2*i+1]*spec_q[2*i+1])*180/(pi)
		#phi=atan((spec_q[2*i]*spec_i[2*i+1]-spec_i[2*i]*spec_q[2*i+1])/(spec_i[2*i]*spec_q[2*i]+spec_i[2*i+1]*spec_q[2*i+1]))*180/(pi)
		if amp_q==0 or amp_i==0 :
                    amp_ratio=0.555555555555555555555555#estos datos son erroneos. Por algun motivo amp_q=0. se reemplazan por 0.555... para que no se caiga el script.
                else: 
                    amp_ratio=amp_i/amp_q# x del paper
                    razon_amplitud_lsb.append([i,amp_ratio])
                    g2.plot(razon_amplitud_lsb)

		phase_dif=(angle_i-angle_q)
		diferencia_fase_lsb.append([i,phase_dif])
		#time.sleep(3)
		#print str(phase_dif)
		#time.sleep(0.1)
		
		#hola = phase_dif
		#print  hola
		g3.plot(diferencia_fase_lsb)
		
                if phase_dif<0:
                    phase_dif=360+phase_dif
                teo_lower.append([(amp_ratio),lo-(2*i)*float(bw)/2048])
		teo_lower.append([phase_dif-180,lo-(2*i)*float(bw)/2048])
                amp_i=trunca(amp_i,2)
                amp_q=trunca(amp_q,2)
                angle_i=trunca(angle_i,2)
                angle_q=trunca(angle_q,2)
		amp_rat=trunca(amp_ratio,2)
		ang_dif=trunca(phase_dif,2) 
		phi=trunca(phi,2)
                #print(str(lo+(2*i)*float(bw)/2048))
                print (trunca(lo-(2*i)*float(bw)/2048,2).rjust(6)+' '+repr(2*i).rjust(10)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7))
                archi.write(trunca(lo-(2*i)*float(bw)/2048,2).rjust(6)+' '+repr(2*i).rjust(10)+' '+trunca(spec_i[2*i],2).rjust(7)+' '+trunca(spec_i[2*i+1],2).rjust(7)+' '+trunca(spec_q[2*i],2).rjust(7)+' '+trunca(spec_q[2*i+1],2).rjust(7)+' '+(amp_i).rjust(7)+' '+(amp_q).rjust(7)+' '+(angle_i).rjust(7)+' '+(angle_q).rjust(7)+' '+(amp_rat).rjust(7)+' '+(ang_dif).rjust(7)+' '+phi.rjust(7)+' \n')
    archi_teo.write('#lower_sideband'+' \n') 
    for i in range(0,len(teo_lower),2):
        archi_teo.write('0 '+str(teo_lower[i][0])+' '+str(teo_lower[i][1])+' \n')
    for i in range(1,len(teo_lower),2):
	archi_teo.write('0 '+str(teo_lower[i][0])+' '+str(teo_lower[i][1])+' \n')
    archi_teo.write('#upper_sideband'+' \n')
    for i in range(0,len(teo_upper),2):
        archi_teo.write('0 '+str(teo_upper[i][0])+' '+str(teo_upper[i][1])+' \n')
    for i in range(1,len(teo_upper),2):
	archi_teo.write('0 '+str(teo_upper[i][0])+' '+str(teo_upper[i][1])+' \n')    
    tf=time.time()
    print('tiempo total='+repr((tf-ti)/60)+' minutos')

   

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

