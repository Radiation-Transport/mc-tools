#!/usr/bin/python2 -W all
#
# https://github.com/kbat/mc-tools
#

from __future__ import print_function
import sys, argparse, struct
from os import path
import numpy as np
from mctools.mcnp.ssw import fortranRead

class PTRAC:
        """PTRAC reader for MCNPX
        """
        def __init__(self,fname,verbose=False):
                self.verbose = verbose
                self.fname=fname
                self.file = open(self.fname, 'rb')
                self.keywords = {} # dictionary of input parameters
                self.nvars    = {} # dictionary of number of variables
                self.event_type = ('src', 'bnk', 'sur', 'col', 'ter')

                data = fortranRead(self.file)
                (i,) =  struct.unpack("=i", data)
                if i!=-1:
                        print("Format error: i=",i)
                        self.file.close()
                        sys.exit(1)
                
                data = fortranRead(self.file)
                (self.code,self.ver,self.loddat,self.idtm,self.rundat)=struct.unpack("=8s5s11s19s17s", data)
                
                self.code = self.code.strip()
                self.ver  = self.ver.strip()
                self.loddat = self.loddat.strip()
                self.idtm = self.idtm.strip()
                self.rundat = self.rundat.strip()

                data = fortranRead(self.file)
                (self.title,) = struct.unpack("=80s", data)
                self.title = self.title.strip()

                if verbose:
                        print("code:    ", self.code)
                        print("ver:     ", self.ver)
                        print("loddat:  ", self.loddat)
                        print("idtm:    ", self.idtm)
                        print("run date:", self.rundat)
                        print("title:   ", self.title)

                # Input data from the PTRAC card used in the MCNPX run
                input_data = []
                data = fortranRead(self.file)
                while len(data) == 40: # 40=4(float size) * 10 numbers per record
                        n = struct.unpack("=10f", data)
                        input_data.append(map(int,n))
                        data = fortranRead(self.file)

                input_data = [item for sublist in input_data for item in sublist] # flatten the PTRAC input_data

                if self.verbose:
                        print("Input keywords array:",input_data,"; length:",len(input_data))

                self.SetKeywords(input_data)

                # now let's unpack the data read last in the previous while loop but the data length was not 40:
                # Numbers of variables N_i:
                N = struct.unpack("=20i", data) # record 4+K
                N = N[0:13] # N14-N20 are not used (page I-2)
                if self.verbose:
                        print("Numbers of variables:",N, len(N))

                self.SetNVars(N)

                # Variable IDs:
                # Number of variables expected for each line type and each event type, i.e NPS line and Event1 and Event2 lines for SRC, BNK, SUR, COL, TER
                # The remaining two variables correspond to the transport particle type (1 for neutron etc. or 0 for multiple particle transport),
                # and whether the output is given in real*4 or real*8
                print("Variable IDs:")
                data = fortranRead(self.file)
                self.vars = struct.unpack("=46i", data)
                print(self.vars, "sum:",sum(self.vars))

                self.ReadEvent()
                
                
        def ReadEvent(self):
                # first NPS line
                print("Event:")
                data = fortranRead(self.file)
                x = struct.unpack("=2i", data) 
                print(x)

        def SetKeywords(self,data):
                # set the input parameters keywords
                # see pages 5-205 and I-3 of the MCNPX manual
                keywords = ('buffer', 'cell', 'event', 'file', 'filter', 'max', 'meph', 'nps', 'surface', 'tally', 'type', 'value', 'write')

                j = 1 # position of n_i
                n = 0 # number of entries for the i-th keyword or 0 for no entries
                for i,k in enumerate(keywords):
                        n = data[j]
                        i1 = 1+j
                        i2 = i1+n
                        if n:
                                self.keywords[k] = data[i1:i2]
                        j=i2

                if self.verbose:
                        print("Number of PTRAC keywords:", data[0])
                        print("Input keywords dict: ",self.keywords)

        def SetNVars(self,data):
                """ Set number of variables on the corresponding event lines (page I-2)"""
                i=1
                for t in self.event_type:
                        self.nvars[t] = data[i:i+2]
                        i = i+2

                if self.verbose:
                        print("Number of variables on the event lines:",self.nvars)
                

def main():
	"""
	PTRAC to TXT converter.

        Assumes that the PTRAC file is generated by MCNPX in binary format.
	"""
	parser = argparse.ArgumentParser(description=main.__doc__,
					 epilog="Homepage: https://github.com/kbat/mc-tools")
	parser.add_argument('ptrac', type=str, help='ptrac binary file name')
	parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose', help='explain what is being done')
        
	args = parser.parse_args()
        
	if not path.isfile(args.ptrac):
		print("ptrac2txt: File %s does not exist." % args.ptrac, file=sys.stderr)
		return 1
        
	p = PTRAC(args.ptrac,args.verbose)
        p.file.close()

if __name__ == "__main__":
        sys.exit(main())
