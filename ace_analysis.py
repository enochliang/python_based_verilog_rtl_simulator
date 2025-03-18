import pprint
import json
import argparse
import pandas as pd
import ast
import re
from igraph import Graph  # Make sure to import igraph

# -------------------
# ERNode Class
# -------------------
class ERNode:
    """
    Represents a node in the Error Propagation (ER) graph, tracking register state over cycles.

    Attributes:
        _reg_name (str): The name of the register this node represents.
        _start (int): The starting cycle of this node's existence.
        end (int): The ending cycle of this node's existence (updated as ER persists).
        parents (list): List of tuples (parent_id, path_type, probability) linking to parent nodes.
        er_type (str): Type of ER node, either "ace" (default) or "unace" (un-ACE interval).

    Properties:
        reg_name (str): Read-only access to the register name.
        start (int): Read-only access to the starting cycle.
    """
    def __init__(self, reg_name: str, start: int):
        self._reg_name = reg_name
        self._start = start
        self.end = start
        self.parents = []
        self.er_type = "ace"

    @property
    def reg_name(self):
        return self._reg_name

    @property
    def start(self):
        return self._start

# -------------------
# RWTableLoader Class
# -------------------
class RWTableLoader:
    """
    Loads and processes a read/write (RW) event table from a CSV file for fault propagation analysis.

    Attributes:
        rw_table_file (str): Path to the CSV file containing RW events (default: "prob_rw_table.csv").
        reg_prop_list (list): List of dictionaries mapping registers to propagation probabilities per cycle.
        rw_table (pd.DataFrame): Loaded RW table as a pandas DataFrame.
        rw_table_list (list): Processed list of RW events per cycle.
        total_cycle (int): Total number of cycles in the RW table.
        start_cyc (int): The starting cycle number from the table.
    """
    def __init__(self, rw_table_file: str = "prob_rw_table.csv"):
        self.rw_table_file = rw_table_file
        self.reg_prop_list = list()

    def load(self):
        """
        Loads the RW table from CSV and processes it into a list of RW events and propagation probabilities.

        The CSV is expected to have columns 'cycle' and 'rw_event', where 'rw_event' is a string representation
        of a list of dictionaries containing read ('r'), write ('w'), stay ('stay'), and control ('ctrl') events.
        """
        self.rw_table = pd.read_csv(self.rw_table_file)
        self.rw_table_list = list()
        self.total_cycle = len(self.rw_table)
        for idx, row in self.rw_table.iterrows():
            cyc = row["cycle"]
            if idx == 0:
                self.start_cyc = cyc

            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            rw_row = {}
            prop_row = {}
            for rw_event in rw_events:
                rw_row[re.sub(r'\bgenblk\d+\.', '', rw_event["r"])] = {"w": set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["w"]]), 
                                         "stay": set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["stay"]]), 
                                         "ctrl": set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["ctrl"]])}
                if len(rw_event["stay"]) > 0:
                    prop_row[re.sub(r'\bgenblk\d+\.', '', rw_event["r"])] = 1.0
                else:
                    mask_probs = [1.0 - prob for dst_reg, prob in set([w_event for w_event in rw_event["w"]] + 
                                                                      [w_event for w_event in rw_event["ctrl"]])]
                    tot_m_probs = 1.0
                    for m_prob in mask_probs:
                        tot_m_probs *= m_prob
                    tot_p_probs = 1.0 - tot_m_probs
                    prop_row[ re.sub(r'\bgenblk\d+\.', '', rw_event["r"]) ] = tot_p_probs

            self.rw_table_list.append(rw_row)
            self.reg_prop_list.append(prop_row)

# -------------------
# AceAnalysis Class
# -------------------
class AceAnalysis:
    """
    Analyzes fault propagation using RW events and constructs a graph representation.

    Attributes:
        sig_dict (dict): Dictionary loaded from a JSON signal table file, containing flip-flop ('ff') registers.
        last_cyc_er_id (dict): Maps registers to the ID of their last ER node in the propagation graph.
        reg_table (dict): Maps registers to their current ERNode object (or None if not active).
        rw_loader (RWTableLoader): Instance for loading and processing RW events.
        rw_table (list): List of processed RW events from RWTableLoader.
        tot_cyc (int): Total number of cycles in the RW table.
        start_cyc (int): Starting cycle from the RW table.
        prop_graph_nodes (list): List of ERNode objects forming the propagation graph.
        prop_graph_links (list): List of tuples (source_id, path, prob, target_id) representing graph edges.
        unACE_int (list): List of indices of un-ACE interval nodes in prop_graph_nodes.
        igraph (Graph): igraph object representing the fault propagation graph (set by igraph_construct).
    """
    def __init__(self, ace_dir: str, sigtable_dir: str):
        f = open(sigtable_dir, "r")
        self.sig_dict = json.load(f)
        f.close()

        self.last_cyc_er_id = {}
        self.reg_table = {}
        self.tot_bit_num = 0
        for reg in self.sig_dict["ff"]:
            self.reg_table[reg] = None
            self.last_cyc_er_id[reg] = None
            self.tot_bit_num += self.sig_dict["ff"][reg]

        self.rw_loader = RWTableLoader(ace_dir)
        self.rw_loader.load()
        self.rw_table = self.rw_loader.rw_table_list
        self.tot_cyc = self.rw_loader.total_cycle
        self.start_cyc = self.rw_loader.start_cyc
        self.tot_fault_num = self.tot_cyc * self.tot_bit_num

        self.prop_graph_nodes = []
        self.prop_graph_links = []
        self.unACE_int = []

    def pre_ace_info(self):
        ctrl_fault_count = 0
        data_fault_count = 0
        for rw_events in self.rw_table:
            for r_reg in rw_events:
                if len(rw_events[r_reg]["ctrl"]) > 0:
                    ctrl_fault_count += self.sig_dict["ff"][r_reg]
                elif len(rw_events[r_reg]["w"]) == 0 and len(rw_events[r_reg]["stay"]) != 0:
                    pass
                else:
                    data_fault_count += self.sig_dict["ff"][r_reg]



        print("[Pre-ACE information]")
        print(f"  - Start Cycle of Simulation: \t{self.start_cyc}")
        print(f"  - Total Number of Simulation Cycles: \t{self.tot_cyc}")
        print(f"  - Total Number of Register Bit: \t{self.tot_bit_num}")
        print(f"  - Total Transient Faults: \t{self.tot_fault_num}")
        print(f"  - ACE remained Faults: \t{data_fault_count+ctrl_fault_count}")
        print(f"  - ACE remained data Faults: \t{data_fault_count}")
        print(f"  - ACE remained ctrl Faults: \t{ctrl_fault_count}")
        print(80*"-")

    def prop_graph_construct(self):
        """
        Constructs the fault propagation graph by creating ER nodes and linking them based on RW events.

        Iterates through cycles, creating ER nodes for registers, connecting them to parents based on write,
        control, and stay events, and marking un-ACE intervals where applicable.
        """
        print("[Propagation Graph Constructing ...]")
        r_event_list = []
        for idx, row in enumerate(self.rw_table):
            self.create_new_er(idx)

            for r_reg in r_event_list:
                r_er_id = self.last_cyc_er_id[r_reg]
                for w_event in self.rw_table[idx-1][r_reg]["w"]:
                    w_reg = w_event[0]
                    prob = w_event[1]
                    self.reg_table[w_reg].parents.append((r_er_id, "w", prob))
                for w_event in self.rw_table[idx-1][r_reg]["ctrl"]:
                    w_reg, prob = w_event
                    self.reg_table[w_reg].parents.append((r_er_id, "ctrl", prob))
                for w_event in self.rw_table[idx-1][r_reg]["stay"]:
                    w_reg, prob = w_event
                    self.reg_table[w_reg].parents.append((r_er_id, "stay", prob))

            r_event_list = []

            for reg in self.sig_dict["ff"]:
                rw_events = self.rw_table[idx]
                if reg not in rw_events:
                    self.unACE_int.append(len(self.prop_graph_nodes))
                    self.last_cyc_er_id[reg] = len(self.prop_graph_nodes)
                    self.reg_table[reg].er_type = "unace"
                    self.prop_graph_nodes.append(self.reg_table[reg])
                    self.reg_table[reg] = None
                elif len(rw_events[reg]["w"]) + len(rw_events[reg]["ctrl"]) > 0:
                    r_event_list.append(reg)
                    self.last_cyc_er_id[reg] = len(self.prop_graph_nodes)
                    self.prop_graph_nodes.append(self.reg_table[reg])
                    self.reg_table[reg] = None
                else:
                    if idx < len(self.rw_table) - 1:
                        self.reg_table[reg].end = self.reg_table[reg].end + 1
        
        for reg in self.sig_dict["ff"]:
            if not self.reg_table[reg]:
                continue
            self.prop_graph_nodes.append(self.reg_table[reg])
            self.reg_table[reg] = None


        self.connect_links()

        tot_bit_mun_er = 0
        for node in self.prop_graph_nodes:
            width = self.sig_dict["ff"][node.reg_name]
            duration = node.end - node.start + 1
            tot_bit_mun_er += width * duration
        print(f"  - Number of Nodes = {len(self.prop_graph_nodes)}")
        print(f"  - Number of Links = {len(self.prop_graph_links)}")
        print(f"  - Total Number of Bit in ERs = {tot_bit_mun_er}")
        print(80*"-")

    def create_new_er(self, idx):
        """
        Creates new ER nodes for registers that lack an active node at the current cycle index.

        Args:
            idx (int): Current cycle index relative to the start cycle.
        """
        for reg in self.reg_table:
            if self.reg_table[reg] == None:
                self.reg_table[reg] = ERNode(reg_name=reg, start=(idx + self.start_cyc))

    def connect_links(self):
        """
        Populates prop_graph_links by connecting each node's parents to its index in prop_graph_nodes.
        """
        for idx, node in enumerate(self.prop_graph_nodes):
            for parent_info in node.parents:
                r_er_id, path, prob = parent_info
                self.prop_graph_links.append((r_er_id, path, prob, idx))

    def igraph_construct(self):
        """
        Constructs an igraph object representing the fault propagation graph.

        Nodes are added from prop_graph_nodes with attributes (reg_name, start, end, er_type).
        Edges are added from prop_graph_links with attributes (path, prob).
        The resulting graph is stored in self.pg_graph.

        Returns:
            Graph: The constructed igraph object.
        """
        g = Graph(directed=True)
        g.add_vertices(len(self.prop_graph_nodes))
        g.vs["reg_name"] = [node.reg_name for node in self.prop_graph_nodes]
        g.vs["start"] = [node.start for node in self.prop_graph_nodes]
        g.vs["end"] = [node.end for node in self.prop_graph_nodes]
        g.vs["er_type"] = [node.er_type for node in self.prop_graph_nodes]

        edges = [(link[0], link[3]) for link in self.prop_graph_links]
        g.add_edges(edges)
        g.es["path"] = [link[1] for link in self.prop_graph_links]
        g.es["prob"] = [link[2] for link in self.prop_graph_links]

        self.pg_graph = g
        print(f"   iGraph constructed:")
        print(f"      Vertices: {g.vcount()}")
        print(f"      Edges: {g.ecount()}")

        return g

    def mark_masked(self):
        """
        Marks tail nodes with 'unace' as 'masked' and propagates the 'masked' status upward in the DAG.
    
        Starts by marking all nodes in self.unACE_int as 'masked'. Then, traverses the graph bottom-up,
        marking a node as 'masked' if all its children (successors) are 'masked'. Updates both the
        prop_graph_nodes list and the igraph object.
    
        Note: Assumes prop_graph_construct() and igraph_construct() have been called to populate the graph.
        """
        # Step 1: Mark all unACE nodes as 'masked' initially
        unace_fault_count = 0
        for node_idx in self.unACE_int:
            node = self.prop_graph_nodes[node_idx]
            reg = node.reg_name
            duration = node.end - node.start + 1
            width = self.sig_dict["ff"][reg]
            unace_fault_count += duration * width
            self.prop_graph_nodes[node_idx].er_type = "masked"
            self.pg_graph.vs[node_idx]["er_type"] = "masked"
    
        # Print the number of initial 'unace' nodes marked as 'masked'
        initial_masked_count = len(self.unACE_int)
        print(f"   Initially marked {initial_masked_count} 'unace' nodes as 'masked'.")
    
        # Step 2: Traverse the graph bottom-up using igraph
        # Get all nodes and their out-degrees (number of children)
        g = self.pg_graph
        out_degrees = g.outdegree()  # List of out-degrees for each vertex
    
        # Process nodes in a topological order (tail nodes first), but we need to check all nodes
        # Use a queue-like approach starting from nodes with no children (tail nodes)
        from collections import deque
        queue = deque([i for i, deg in enumerate(out_degrees) if deg == 0])
        visited = set()  # To avoid reprocessing nodes
    
        while queue:
            node_idx = queue.popleft()
            if node_idx in visited:
                continue
            visited.add(node_idx)
    
            # Check if all children of this node are 'masked'
            children = g.successors(node_idx)  # List of child indices
            if children:  # If node has children
                all_children_masked = all(g.vs[child]["er_type"] == "masked" for child in children)
                if all_children_masked:
                    # Mark the current node as 'masked' in both structures
                    self.prop_graph_nodes[node_idx].er_type = "masked"
                    g.vs[node_idx]["er_type"] = "masked"
    
            # Add parents (predecessors) to the queue if all their children have been processed
            parents = g.predecessors(node_idx)
            for parent_idx in parents:
                parent_children = g.successors(parent_idx)
                if all(child in visited for child in parent_children):
                    queue.append(parent_idx)
    
        # Step 3: Print summary for verification
        masked_count = sum(1 for node in self.prop_graph_nodes if node.er_type == "masked")
        self.unace_fault_count = unace_fault_count
        dup_fault_count = sum(self.sig_dict["ff"][node.reg_name]*(node.end-node.start+1) for node in self.prop_graph_nodes if node.er_type == "masked") - unace_fault_count
        self.dup_fault_count = dup_fault_count
        redundant_eq_fault_count = sum(self.sig_dict["ff"][node.reg_name]*(node.end-node.start) for node in self.prop_graph_nodes if node.er_type == "ace")
        self.redundant_eq_fault_count = redundant_eq_fault_count
        self.remained_fault = self.tot_fault_num - unace_fault_count - dup_fault_count - redundant_eq_fault_count
        print(f"   Marked {masked_count} nodes as 'masked' in the graph.")

        print(f"   - un-ACE fault count = {unace_fault_count}")
        print(f"   - DUP fault count = {dup_fault_count}")
        print(f"   - redundant equvalent fault count = {redundant_eq_fault_count}")

    def count_ace(self):
        unace_fault_count = sum(self.sig_dict["ff"][node.reg_name]*(node.end-node.start+1) for node in self.prop_graph_nodes if node.er_type == "unace")
        redundant_eq_fault_count = sum(self.sig_dict["ff"][node.reg_name]*(node.end-node.start) for node in self.prop_graph_nodes if node.er_type == "ace")
        print(f"   - un-ACE fault count = {unace_fault_count}")
        print(f"   - redundant equvalent fault count = {redundant_eq_fault_count}")

    def output_pruned_rw_table(self, prune_flag=True):
        self.rw_table_pruned = {"cycle":[cyc for cyc in range(self.start_cyc, self.start_cyc+self.tot_cyc)],"rw_event":[[]]*self.tot_cyc}
        start_cyc = self.start_cyc
        for idx, node in enumerate(self.prop_graph_nodes):
            if node.er_type == "ace":
                r_reg = node.reg_name
                r_cyc = node.end
                rw_event = self.rw_table[r_cyc-start_cyc][r_reg]
                new_rw_event = {"r":r_reg, 
                                "w":list(rw_event["w"]),
                                "ctrl":list(rw_event["ctrl"]),
                                "stay":list(rw_event["stay"]),
                                "start_cyc":node.start,
                                "end_cyc":node.end}
                self.rw_table_pruned["rw_event"][r_cyc-start_cyc] = self.rw_table_pruned["rw_event"][r_cyc-start_cyc]+[new_rw_event]
        #pprint.pp(self.rw_table_pruned)

        df = pd.DataFrame(self.rw_table_pruned)
        if not prune_flag:
            new_rw_table_dir = rw_table_dir.replace(".csv","")+"_unpruned.csv"    
        else:
            new_rw_table_dir = rw_table_dir.replace(".csv","")+"_pruned.csv"
        df.to_csv(new_rw_table_dir)
        #ace_result = {"total_fault":self.tot_fault_num,
        #              "unACE_fault":self.unace_fault_count,
        #              "dup_fault":self.dup_fault_count,
        #              "eq_fault":self.redundant_eq_fault_count,
        #              "remain_fault":self.remained_fault
        #              }
        print(f"Dumped Pruned RW-table file: <{new_rw_table_dir}>")



# -------------------
# Main Execution
# -------------------
if __name__ == "__main__":
    """
    Entry point for the script. Parses command-line arguments and runs the ACE analysis.

    Command-line Arguments:
        --rw_table_dir (str): Path to the RW table CSV file.
        --sig_list_dir (str): Path to the signal table JSON file.
    """
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")
    parser.add_argument('--rw_table_dir', type=str, help='RW-table directory')
    parser.add_argument("--sig_list_dir", type=str, help="Logic value path")
    parser.add_argument("--prune", action='store_true', help="Pruning Flag")
    args = parser.parse_args()

    rw_table_dir = args.rw_table_dir
    sig_list_dir = args.sig_list_dir

    ace = AceAnalysis(ace_dir=rw_table_dir, sigtable_dir=sig_list_dir)
    ace.pre_ace_info()
    ace.prop_graph_construct()
    g = ace.igraph_construct()
    if args.prune:
        ace.mark_masked()  # Add this line to apply the masking logic
        ace.output_pruned_rw_table(prune_flag=True)
    else:
        ace.count_ace()
        ace.output_pruned_rw_table(prune_flag=False)
