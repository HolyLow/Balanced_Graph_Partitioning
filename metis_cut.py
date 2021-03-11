import numpy as np
import subprocess
import os.path
from snudda.analyse_connection import SnuddaAnalyseConnection

class MetisCut(object):

    def __init__(self, in_file, exe_file):
        self.in_file = in_file
        self.snudda_analyser = SnuddaAnalyseConnection(in_file)
        self.exe_file = exe_file
    
    def default_cut(self, npartition, nmachine, enable_multicut, gapJunction_scale):
        self.synapse_cut(npartition, nmachine, enable_multicut)
        # self.gapJunction_cut(npartition, nmachine, enable_multicut)
        self.hybrid_cut(npartition, nmachine, enable_multicut, gapJunction_scale)
        
    def synapse_cut(self, npartition, nmachine, enable_multicut):
        cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
        synapse_con_mat = self.snudda_analyser.create_con_mat("synapses")
        synapse_distribution = self.multi_machine_partition(synapse_con_mat, npartition, nmachine, enable_multicut)
        self.snudda_analyser.analyse_partition_cut(synapse_con_mat, cut_penalty_mat, synapse_distribution, npartition)
        fingerprint = "synapse-metis-partition" + str(synapse_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
        if enable_multicut:
            fingerprint += "-enableMulticut"
        else:
            fingerprint += "-disableMulticut"
        self.export_partition_to_csv(synapse_distribution, fingerprint)
        
    def gapJunction_cut(self, npartition, nmachine, enable_multicut):
        cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
        gapJunction_con_mat = self.snudda_analyser.create_con_mat("gapJunctions")
        gapJunction_distribution = self.multi_machine_partition(gapJunction_con_mat, npartition, nmachine, enable_multicut)
        self.snudda_analyser.analyse_partition_cut(gapJunction_con_mat, cut_penalty_mat, gapJunction_distribution, npartition)
        fingerprint = "gapJunction-metis-partition" + str(gapJunction_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
        if enable_multicut:
            fingerprint += "-enableMulticut"
        else:
            fingerprint += "-disableMulticut"
        self.export_partition_to_csv(gapJunction_distribution, fingerprint)
        
    def hybrid_cut(self, npartition, nmachine, enable_multicut, gapJunction_scale):
        cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
        synapse_con_mat = self.snudda_analyser.create_con_mat("synapses")
        gapJunction_con_mat = self.snudda_analyser.create_con_mat("gapJunctions")
        hybrid_con_mat = np.add(synapse_con_mat, np.multiply(gapJunction_con_mat, gapJunction_scale))
        hybrid_distribution = self.multi_machine_partition(hybrid_con_mat, npartition, nmachine, enable_multicut)
        self.snudda_analyser.analyse_partition_cut(hybrid_con_mat, cut_penalty_mat, hybrid_distribution, npartition)
        fingerprint = "hybrid-metis-partition" + str(hybrid_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
        if enable_multicut:
            fingerprint += "-enableMulticut"
        else:
            fingerprint += "-disableMulticut"
        self.export_partition_to_csv(hybrid_distribution, fingerprint)

    def multi_machine_partition(self, con_mat, multi_machine_partition, nmachine, enable_multicut):
        # assert nmachine == 1, "unsupported multi machine partition"
        assert multi_machine_partition >= nmachine, "partition number is smaller than machine number"
        assert multi_machine_partition % nmachine == 0, "partition number can't be equally fit into machine number"

        if nmachine == 1 or not enable_multicut:
            multi_machine_distribution = self.graph_partition(con_mat, multi_machine_partition)
            return multi_machine_distribution

        multi_machine_distribution = np.zeros(con_mat.shape[0], dtype=int)
        across_machine_distribution = self.graph_partition(con_mat, nmachine)
        single_machine_partition = multi_machine_partition // nmachine
        for machine_id in range(nmachine):
            machine_nodes = []
            for i in range(across_machine_distribution.shape[0]):
                if across_machine_distribution[i] == machine_id:
                    machine_nodes.append(i)
            subgraph_global_distribution = self.subgraph_partition(con_mat, machine_nodes, single_machine_partition, single_machine_partition*machine_id)
            multi_machine_distribution = np.add(multi_machine_distribution, subgraph_global_distribution)
        return multi_machine_distribution

    def subgraph_partition(self, con_mat, subgraph_nodes, npartition, offset):
        subgraph_con_mat = np.zeros((len(subgraph_nodes), len(subgraph_nodes)), dtype=int)
        for i in range(subgraph_con_mat.shape[0]):
            for j in range(subgraph_con_mat.shape[1]):
                subgraph_con_mat[i][j] = con_mat[subgraph_nodes[i]][subgraph_nodes[j]]
        subgraph_distribution = self.graph_partition(subgraph_con_mat, npartition)
        subgraph_global_distribution = np.zeros(con_mat.shape[0], dtype=int)
        for i in range(len(subgraph_nodes)):
            subgraph_global_distribution[subgraph_nodes[i]] = subgraph_distribution[i] + offset
        return subgraph_global_distribution

    def graph_partition(self, con_mat, npartition):
        graph_file = "metis-graph.txt"
        self.export_connection_matrix_to_metis_graph(con_mat, graph_file)

        self.run_metis_partition(graph_file, npartition)

        distribution = self.load_metis_partition_result(graph_file, npartition)
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

    def load_metis_partition_result(self, graph_file, npartition):
        distribution_file = graph_file + ".part." + str(npartition)
        distribution = np.loadtxt(distribution_file, delimiter=",", dtype="int")
        max_id = np.max(distribution)
        assert max_id == npartition - 1, "infile nhost mismatched"
        return distribution

    def export_partition_to_csv(self, distribution, fingerprint):
        save_dir = os.path.dirname(self.in_file)
        save_csv = save_dir + "/" + fingerprint + ".csv"
        np.savetxt(save_csv, distribution, delimiter=",", fmt="%d")
        print("write to %s done" % save_csv)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Metis cut")
    parser.add_argument("inFile", help="Snudda HDF5 file with network")
    parser.add_argument("exeFile", help="Metis partition binary executable file")
    parser.add_argument("npartition", type=int, help="partition npartition")
    parser.add_argument("--gapJunctionScale", "--gapJunctionScale", type=int, default=1000, help="Scale of a gapJunction relative to a synapse")
    parser.add_argument("--nmachine", "--nmachine", type=int, default=1, help="Number of machines the partitions would distribute to equally")
    parser.add_argument('--multicut', dest='enableMulticut', action='store_true', default=False, help='Enable the multicut algorithm')
    args = parser.parse_args()
    
    metis_cut = MetisCut(args.inFile, args.exeFile)
    metis_cut.default_cut(args.npartition, args.nmachine, args.enableMulticut, args.gapJunctionScale)