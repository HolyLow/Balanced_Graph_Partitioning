
import numpy as np

class AnalyseCut(object):

    def __init__(self, inFile, nhost):
        self.nhost = nhost
        self.distribution = np.loadtxt(inFile, delimiter=",", dtype="int")
        maxID = np.max(self.distribution)
        if maxID != self.nhost - 1:
            assert False, "infile nhost mismatched"

    def analyse(self):
        nhostCnts = np.zeros(self.nhost, dtype="int")
        for hostID in self.distribution:
            nhostCnts[hostID] += 1
        print(nhostCnts)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="analyse graph cut")
    parser.add_argument("inFile", help="Input graph cut file, in numpy format")
    # parser.add_argument("outFile", help="Output partition result file, in numpy format")
    parser.add_argument("k", type=int, help="Partition number")
    args = parser.parse_args()
    
    analyseCut = AnalyseCut(args.inFile, args.k)
    analyseCut.analyse()