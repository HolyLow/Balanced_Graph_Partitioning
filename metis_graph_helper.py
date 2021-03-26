import numpy as np
import subprocess
import os.path
import sys

class MetisGraphHelper(object):

    def __init__(self, metisUndirectedGraphFile, partitionNum, hyperMetisGraphFiles, metisDistFiles):
        self.metisUndirectedGraphFile = metisUndirectedGraphFile
        self.metisUndirectedGraph = self.loadMetisFileToGraphListDict(self.metisUndirectedGraphFile)
        self.partitionNum = partitionNum
        self.hyperMetisGraphFiles = hyperMetisGraphFiles
        self.hyperMetisGraphs = []
        for hyperMetisGraphFile in self.hyperMetisGraphFiles:
            self.hyperMetisGraphs.append(self.loadHyperMetisFileToHypergraphListList(hyperMetisGraphFile))
        self.metisDistFiles = metisDistFiles
        self.metisDists = []
        for metisDistFile in self.metisDistFiles:
            self.metisDists.append(self.loadDistributionFileToDistributionArray(metisDistFile))

    def analyze(self):
        nodeNum = len(self.metisUndirectedGraph)
        roundRobinDistribution = self.generateRoundRobinDistributionArray(nodeNum, self.partitionNum)
        self.analyzeDistribution("RoundRobin", roundRobinDistribution)

        continuousSegmentDistribution = self.generateContinuousSegmentDistributionArray(nodeNum, self.partitionNum)
        self.analyzeDistribution("ContinuousSegment", continuousSegmentDistribution)

        for i in range(len(self.metisDists)):
            self.analyzeDistribution(self.metisDistFiles[i], self.metisDists[i])

    def analyzeDistribution(self, distributionName, distributionArray):
        print("analyzing {} distribution...".format(distributionName))
        cut = self.analyzeGraphDistributionCut(self.metisUndirectedGraph, distributionArray, True)
        print("{} {} undirected graph cut = {}".format(distributionName, self.metisUndirectedGraphFile, cut))
        for i in range(len(self.hyperMetisGraphs)):
            cut = self.analyzeHyperGraphDistributionCut(self.hyperMetisGraphs[i], distributionArray)
            print("{} {} hyper graph cut = {}".format(distributionName, self.hyperMetisGraphFiles[i], cut))

    def loadMetisFileToGraphListDict(self, filename):
        with open(filename, 'r') as f:
            line = f.readline()
            vars = list(filter(lambda x : x, line.split(' ')))
            nodeNum = int(vars[0])
            connNum = int(vars[1])
            graphListDict = []
            for i in range(nodeNum):
                line = f.readline()
                nodeEdgeDict = dict()
                vars = list(filter(lambda x : x, line.split(' ')))
                connCnt = len(vars) // 2
                for j in range(connCnt):
                    nodeEdgeDict[int(vars[j*2])-1] = int(vars[j*2+1])
                graphListDict.append(nodeEdgeDict)
        return graphListDict

    def loadHyperMetisFileToHypergraphListList(self, filename):
        hypergraphListList = []
        with open(filename, 'r') as f:
            line = f.readline()
            vars = list(filter(lambda x : x, line.split(' ')))
            hypergraphListList.append([])
            hypergraphListList[0].append(int(vars[0]))
            hypergraphListList[0].append(int(vars[1]))
            hypergraphListList[0].append(int(vars[2]))
            if hypergraphListList[0][2] != 1:
                print("error: input unsupported hypermetis format {}".format(hypergraphListList[0][2]))
                sys.exit(1)
            for i in range(hypergraphListList[0][0]):
                line = f.readline()
                vars = list(filter(lambda x : x, line.split(' ')))
                hypergraphListList.append([])
                hypergraphListList[i+1].append(int(vars[0]))
                for j in range(1, len(vars)):
                    hypergraphListList[i+1].append(int(vars[j])-1)      # metis node starts at 1, reset to start 0
        if len(hypergraphListList)-1 != hypergraphListList[0][0]:
            print("error: hypergraph hyperEdge num mismatch: {} vs {}".format(hypergraphListList[0][0], len(hypergraphListList)-1))
        print("load {} hyperGraph done, edge {}, node {}".format(filename, hypergraphListList[0][0], hypergraphListList[0][1]))
        return hypergraphListList

    def loadDistributionFileToDistributionArray(self, filename):
        distributionArray = np.loadtxt(filename, delimiter=",", dtype="int")
        maxId = np.max(distributionArray)
        print("distribution file {} partitionNum = {}".format(filename, maxId+1))
        return distributionArray

    def analyzeRoundRobinCut(self, partitionNum):
        distributionArray = self.generateRoundRobinDistributionArray(len(self.undirectedListDict), partitionNum)
        cut = self.analyzeGraphDistributionCut(self.undirectedListDict, distributionArray, True)
        nodeCut = self.analyzeGraphDistributionNodeCut(self.directedListDict, distributionArray)
        print("RoundRobin cut = {}, nodeCut = {}".format(cut, nodeCut))

    def analyzeContinuousSegmentCut(self, partitionNum):
        distributionArray = self.generateContinuousSegmentDistributionArray(len(self.undirectedListDict), partitionNum)
        cut = self.analyzeGraphDistributionCut(self.undirectedListDict, distributionArray, True)
        nodeCut = self.analyzeGraphDistributionNodeCut(self.directedListDict, distributionArray)
        print("ContinuousSegment cut = {}, nodeCut = {}".format(cut, nodeCut))

    def analyzeMetisCut(self, metisDistributionFile):
        distributionArray = self.loadDistributionFileToDistributionArray(metisDistributionFile)
        cut = self.analyzeGraphDistributionCut(self.undirectedListDict, distributionArray, True)
        nodeCut = self.analyzeGraphDistributionNodeCut(self.directedListDict, distributionArray)
        print("{} cut = {}, nodeCut = {}".format(metisDistributionFile, cut, nodeCut))
    
    def analyzeGraphDistributionCut(self, graphListDict, distributionArray, isUndirected):
        partitionNum = np.max(distributionArray) + 1
        cutMatrix = np.zeros((partitionNum, partitionNum), dtype=int)
        for srcNodeId in range(len(graphListDict)):
            nodeEdgeDict = graphListDict[srcNodeId]
            for desNodeId, cnt in nodeEdgeDict.items():
                cutMatrix[distributionArray[srcNodeId]][distributionArray[desNodeId]] += cnt
        cut = 0
        for i in range(partitionNum):
            for j in range(partitionNum):
                if i != j:
                    cut += cutMatrix[i][j]
        if isUndirected:
            cut /= 2
        return cut

    def analyzeGraphDistributionNodeCut(self, graphListDict, distributionArray):
        partitionNum = np.max(distributionArray) + 1
        nodeNum = len(graphListDict)
        cutMatrix = np.zeros((partitionNum, partitionNum), dtype=int)
        partitionNodeEdgeCnts = np.zeros((partitionNum, nodeNum), dtype=int)
        for srcNodeId in range(nodeNum):
            nodeEdgeDict = graphListDict[srcNodeId]
            for desNodeId, cnt in nodeEdgeDict.items():
                partitionNodeEdgeCnts[distributionArray[desNodeId]][srcNodeId] += cnt
        nodeCut = 0
        for i in range(partitionNum):
            for j in range(nodeNum):
                if partitionNodeEdgeCnts[i][j] != 0:
                    nodeCut += 1
        return nodeCut
    
    def analyzeHyperGraphDistributionCut(self, hyperGraphListList, distributionArray):
        if hyperGraphListList[0][2] != 1:
            print("error: unsupported hypergraph type {}".format(hyperGraphListList[0][2]))
            sys.exit(1)
        partitionNum = np.max(distributionArray) + 1
        hyperCut = 0
        for i in range(1, len(hyperGraphListList)):
            hyperEdge = hyperGraphListList[i]
            weight = hyperEdge[0]
            distributionCnt = np.zeros(partitionNum, dtype=int)
            for j in range(1, len(hyperEdge)):
                distributionCnt[distributionArray[hyperEdge[j]]] += 1
            edgeCut = 0
            for j in range(partitionNum):
                if distributionCnt[j] != 0:
                    edgeCut += 1
            hyperCut += (edgeCut-1) * weight
        return hyperCut

    def generateRoundRobinDistributionArray(self, nodeNum, partitionNum):
        distributionArray = np.zeros(nodeNum, dtype=int)
        for nodeId in range(nodeNum):
            distributionArray[nodeId] = nodeId % partitionNum
        return distributionArray

    def generateContinuousSegmentDistributionArray(self, nodeNum, partitionNum):
        distributionArray = np.zeros(nodeNum, dtype=int)
        partitionSize = nodeNum // partitionNum
        addtionalSize = nodeNum % partitionNum
        nodeCnt = 0
        for partition in range(partitionNum):
            segSize = partitionSize
            if partition < addtionalSize:
                segSize += 1
            for i in range(segSize):
                distributionArray[nodeCnt] = partition
                nodeCnt += 1
        if nodeCnt != nodeNum:
            print("error: nodeCnt and nodeNum mismatched, {} vs {}".format(nodeCnt, nodeNum))
        return distributionArray



    # def default_cut(self, npartition, nmachine, enable_multicut, gapJunction_scale):
    #     self.synapse_cut(npartition, nmachine, enable_multicut)
    #     # self.gapJunction_cut(npartition, nmachine, enable_multicut)
    #     self.hybrid_cut(npartition, nmachine, enable_multicut, gapJunction_scale)
        
    # def synapse_cut(self, npartition, nmachine, enable_multicut):
    #     cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
    #     synapse_con_mat = self.snudda_analyser.create_con_mat("synapses")
    #     synapse_distribution = self.multi_machine_partition(synapse_con_mat, npartition, nmachine, enable_multicut)
    #     self.snudda_analyser.analyse_partition_cut(synapse_con_mat, cut_penalty_mat, synapse_distribution, npartition)
    #     fingerprint = "synapse-metis-partition" + str(synapse_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
    #     if enable_multicut:
    #         fingerprint += "-enableMulticut"
    #     else:
    #         fingerprint += "-disableMulticut"
    #     self.export_partition_to_csv(synapse_distribution, fingerprint)
        
    # def gapJunction_cut(self, npartition, nmachine, enable_multicut):
    #     cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
    #     gapJunction_con_mat = self.snudda_analyser.create_con_mat("gapJunctions")
    #     gapJunction_distribution = self.multi_machine_partition(gapJunction_con_mat, npartition, nmachine, enable_multicut)
    #     self.snudda_analyser.analyse_partition_cut(gapJunction_con_mat, cut_penalty_mat, gapJunction_distribution, npartition)
    #     fingerprint = "gapJunction-metis-partition" + str(gapJunction_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
    #     if enable_multicut:
    #         fingerprint += "-enableMulticut"
    #     else:
    #         fingerprint += "-disableMulticut"
    #     self.export_partition_to_csv(gapJunction_distribution, fingerprint)
        
    # def hybrid_cut(self, npartition, nmachine, enable_multicut, gapJunction_scale):
    #     cut_penalty_mat = self.snudda_analyser.analyze_cut_penalty(npartition, nmachine)
    #     synapse_con_mat = self.snudda_analyser.create_con_mat("synapses")
    #     gapJunction_con_mat = self.snudda_analyser.create_con_mat("gapJunctions")
    #     hybrid_con_mat = np.add(synapse_con_mat, np.multiply(gapJunction_con_mat, gapJunction_scale))
    #     hybrid_distribution = self.multi_machine_partition(hybrid_con_mat, npartition, nmachine, enable_multicut)
    #     self.snudda_analyser.analyse_partition_cut(hybrid_con_mat, cut_penalty_mat, hybrid_distribution, npartition)
    #     fingerprint = "hybrid-metis-partition" + str(hybrid_con_mat.shape[0]) + "-" + str(npartition) + "-" + str(nmachine)
    #     if enable_multicut:
    #         fingerprint += "-enableMulticut"
    #     else:
    #         fingerprint += "-disableMulticut"
    #     self.export_partition_to_csv(hybrid_distribution, fingerprint)

    # def multi_machine_partition(self, con_mat, multi_machine_partition, nmachine, enable_multicut):
    #     # assert nmachine == 1, "unsupported multi machine partition"
    #     assert multi_machine_partition >= nmachine, "partition number is smaller than machine number"
    #     assert multi_machine_partition % nmachine == 0, "partition number can't be equally fit into machine number"

    #     if nmachine == 1 or not enable_multicut:
    #         multi_machine_distribution = self.graph_partition(con_mat, multi_machine_partition)
    #         return multi_machine_distribution

    #     multi_machine_distribution = np.zeros(con_mat.shape[0], dtype=int)
    #     across_machine_distribution = self.graph_partition(con_mat, nmachine)
    #     single_machine_partition = multi_machine_partition // nmachine
    #     for machine_id in range(nmachine):
    #         machine_nodes = []
    #         for i in range(across_machine_distribution.shape[0]):
    #             if across_machine_distribution[i] == machine_id:
    #                 machine_nodes.append(i)
    #         subgraph_global_distribution = self.subgraph_partition(con_mat, machine_nodes, single_machine_partition, single_machine_partition*machine_id)
    #         multi_machine_distribution = np.add(multi_machine_distribution, subgraph_global_distribution)
    #     return multi_machine_distribution

    # def subgraph_partition(self, con_mat, subgraph_nodes, npartition, offset):
    #     subgraph_con_mat = np.zeros((len(subgraph_nodes), len(subgraph_nodes)), dtype=int)
    #     for i in range(subgraph_con_mat.shape[0]):
    #         for j in range(subgraph_con_mat.shape[1]):
    #             subgraph_con_mat[i][j] = con_mat[subgraph_nodes[i]][subgraph_nodes[j]]
    #     subgraph_distribution = self.graph_partition(subgraph_con_mat, npartition)
    #     subgraph_global_distribution = np.zeros(con_mat.shape[0], dtype=int)
    #     for i in range(len(subgraph_nodes)):
    #         subgraph_global_distribution[subgraph_nodes[i]] = subgraph_distribution[i] + offset
    #     return subgraph_global_distribution

    # def graph_partition(self, con_mat, npartition):
    #     graph_file = "metis-graph.txt"
    #     self.export_connection_matrix_to_metis_graph(con_mat, graph_file)

    #     self.run_metis_partition(graph_file, npartition)

    #     distribution = self.load_metis_partition_result(graph_file, npartition)
    #     return distribution

    # def export_connection_matrix_to_metis_graph(self, con_mat, graph_file):
    #     graph = ""
    #     con_cnt = 0
    #     for i in range(con_mat.shape[0]):
    #         node = ""
    #         for j in range(con_mat.shape[1]):
    #             if i == j:
    #                 continue
    #             con = con_mat[i][j] + con_mat[j][i]
    #             if con > 0:
    #                 node += str(j+1) + " " + str(con) + " "  # metis node numbering starts from 1
    #                 con_cnt += 1
    #         graph += node + "\n"
    #     con_cnt /= 2
    #     with open(graph_file, "w") as f:
    #         f.write("%d %d 001\n" % (con_mat.shape[0], con_cnt))
    #         f.write(graph)

    # def run_metis_partition(self, graph_file, npartition):
    #     cmd = self.exe_file + " " + graph_file + " " + str(npartition)
    #     status, output = subprocess.getstatusoutput(cmd)
    #     assert status == 0, "command status is not success"
    #     print(output)

    # def load_metis_partition_result(self, graph_file, npartition):
    #     distribution_file = graph_file + ".part." + str(npartition)
    #     distribution = np.loadtxt(distribution_file, delimiter=",", dtype="int")
    #     max_id = np.max(distribution)
    #     assert max_id == npartition - 1, "infile nhost mismatched"
    #     return distribution

    # def export_partition_to_csv(self, distribution, fingerprint):
    #     save_dir = os.path.dirname(self.in_file)
    #     save_csv = save_dir + "/" + fingerprint + ".csv"
    #     np.savetxt(save_csv, distribution, delimiter=",", fmt="%d")
    #     print("write to %s done" % save_csv)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="MetisGraphHelper")
    parser.add_argument("metisUndirectedGraphFile", help="metis undirected graph file")
    # parser.add_argument("directedFile", help="metis directed graph file")
    parser.add_argument("partitionNum", type=int, help="partition npartition")
    parser.add_argument("--hyperMetisGraphFile", "--hyperMetisGraphFile", dest="hyperMetisGraphFiles", action="append", help="hypermetis graph file(s)")
    parser.add_argument("--metisDistFile", "--metisDistFile", dest='metisDistFiles', action='append', help="metis partition distribution file(s)")
    
    # parser.add_argument("exeFile", help="Metis partition binary executable file")
    # parser.add_argument("--gapJunctionScale", "--gapJunctionScale", type=int, default=1000, help="Scale of a gapJunction relative to a synapse")
    # parser.add_argument("--nmachine", "--nmachine", type=int, default=1, help="Number of machines the partitions would distribute to equally")
    # parser.add_argument('--multicut', dest='enableMulticut', action='store_true', default=False, help='Enable the multicut algorithm')
    args = parser.parse_args()

    metisGraphHelper = MetisGraphHelper(args.metisUndirectedGraphFile, args.partitionNum, args.hyperMetisGraphFiles, args.metisDistFiles)
    metisGraphHelper.analyze()
    # metisGraphHelper.analyzeRoundRobinCut(args.partitionNum)
    # metisGraphHelper.analyzeContinuousSegmentCut(args.partitionNum)
    # for metisDistFile in args.metisDistFiles:
    #     metisGraphHelper.analyzeMetisCut(metisDistFile)
    # if len(args.hyperMetisGraphFiles) != len(args.hyperMetisDistFiles):
    #     print("hyperMeits graph and dist file num mismatch")
    #     sys.exit(1)
    # for i in range(len(args.hyperMetisGraphFiles)):
    #     metisGraphHelper.analyzeHyperMetisCut(args.hyperMetisGraphFiles[i], args.hyperMetisDistFiles[i])
    # if args.metisDistFile != None:
        # metisGraphHelper.analyzeMetisCut(args.metisDistFile)
    
    # metis_cut = MetisCut(args.undirectedFile, args.exeFile)
    # metis_cut.default_cut(args.npartition, args.nmachine, args.enableMulticut, args.gapJunctionScale)