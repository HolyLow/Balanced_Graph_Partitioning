import numpy as np
import subprocess
from snudda.analyse_connection import SnuddaAnalyseConnection

class MetisCut(object):

    def __init__(self, in_file, exe_file, npartition, nmachine, gapJunction_scale):
        self.snudda_analyser = SnuddaAnalyseConnection(in_file)
        self.exe_file = exe_file
        
        cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)

        synapse_con_mat = self.snudda_analyser.create_con_mat("synapses")
        synapse_distribution = self.multi_machine_partition(synapse_con_mat, npartition, nmachine)
        self.snudda_analyser.analyse_partition_cut(synapse_con_mat, cut_penalty_mat, synapse_distribution, npartition)

    def multi_machine_partition(self, con_mat, npartition, nmachine):
        assert nmachine == 1, "unsupported multi machine partition"

        distribution = self.single_machine_partition(con_mat, npartition)
        return distribution

    def single_machine_partition(self, con_mat, npartition):
        graph_file = "metis-graph.txt"
        self.export_connection_matrix_to_metis_graph(con_mat, graph_file)

        self.run_metis_partition(graph_file, npartition)

        distribution = self.load_metis_partion_result(graph_file, npartition)
        return distribution

    def export_connection_matrix_to_metis_graph(self, con_mat, graph_file):
        graph = ""
        con_cnt = 0
        for i in range(con_mat.shape[0]):
            node = ""
            for j in range(con_mat.shape[1]):
                if i == j:
                    continue
                con = con_mat[i][j] + con_mat[j][i]
                if con > 0:
                    node += str(j+1) + " " + str(con) + " "  # metis node numbering starts from 1
                    con_cnt += 1
            graph += node + "\n"
        con_cnt /= 2
        with open(graph_file, "w") as f:
            f.write("%d %d 001\n" % (con_mat.shape[0], con_cnt))
            f.write(graph)

    def run_metis_partition(self, graph_file, npartition):
        cmd = self.exe_file + " " + graph_file + " " + str(npartition)
        status, output = subprocess.getstatusoutput(cmd)
        assert status == 0, "command status is not success"
        print(output)

    def load_metis_partion_result(self, graph_file, npartition):
        distribution_file = graph_file + ".part." + str(npartition)
        distribution = np.loadtxt(distribution_file, delimiter=",", dtype="int")
        max_id = np.max(distribution)
        assert max_id == npartition - 1, "infile nhost mismatched"
        return distribution
        
if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Metis cut")
    parser.add_argument("inFile", help="Snudda HDF5 file with network")
    parser.add_argument("exeFile", help="Metis partition binary executable file")
    parser.add_argument("npartition", type=int, help="partition npartition")
    parser.add_argument("--gapJunctionScale", "--gapJunctionScale", type=int, default=1000, help="Scale of a gapJunction relative to a synapse")
    parser.add_argument("--nmachine", "--nmachine", type=int, default=1, help="Number of machines the partitions would distribute to equally")
    args = parser.parse_args()
    
    metis_cut = MetisCut(args.inFile, args.exeFile, args.npartition, args.nmachine, args.gapJunctionScale)