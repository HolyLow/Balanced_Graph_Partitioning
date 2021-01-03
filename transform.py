import numpy as np

class Transform(object):
    def __init__(self, inFile, outFile):
        self.inFile = inFile
        self.outFile = outFile

    def transform(self, option):
        if option == "numpyAdjacentMatrix2metisGraph":
            self.transformNumpyAdjacentMatrix2metisGraph()
        # elif option == "metisPartition2numpyArray":
        #     self.transformMetisPartition2numpyArray()
        else:
            assert False, "transform option undefined"

    def transformNumpyAdjacentMatrix2metisGraph(self):
        conMat = np.loadtxt(self.inFile, delimiter=",", dtype="int")
        graph = ""
        conCnt = 0
        for i in range(conMat.shape[0]):
            node = ""
            for j in range(conMat.shape[1]):
                if i == j:
                    continue
                con = conMat[i][j] + conMat[j][i]
                if con > 0:
                    node += str(j+1) + " " + str(con) + " "  # metis node numbering starts from 1
                    conCnt += 1
            graph += node + "\n"
        conCnt /= 2
        with open(self.outFile, "w") as f:
            f.write("%d %d 001\n" % (conMat.shape[0], conCnt))
            f.write(graph)

    # def transformNumpyAdjacentMatrix2metisGraph(self):
        

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="analyse graph cut")
    parser.add_argument("inFile", help="Input file")
    parser.add_argument("outFile", help="Output file")
    parser.add_argument("option", help="File transformation type")
    args = parser.parse_args()

    transform = Transform(args.inFile, args.outFile)
    transform.transform(args.option)