import json
import argparse
import pandas as pd
import ast


class ERNode:
    def __init__(self, reg_name:str,start:int):
        self._reg_name = reg_name
        self._start = start
        self.end = start
        self.parents = []
    
    @property
    def reg_name(self):
        return self._reg_name

    @property
    def start(self):
        return self._start

    

class RWTableLoader:
    def __init__(self,rw_table_file:str="prob_rw_table.csv"):
        self.rw_table_file = rw_table_file
        self.reg_prop_list = list()
    
    def load(self):
        self.rw_table = pd.read_csv(self.rw_table_file)
        self.rw_table_list = list()
        self.total_cycle = len(self.rw_table)
        for idx , row in self.rw_table.iterrows():
            cyc = row["cycle"]
            if idx == 0:
                self.start_cyc = cyc

            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            rw_row = {}
            prop_row = {}
            for rw_event in rw_events:
                rw_row[rw_event["r"]] = {"w":set([w_event for w_event in rw_event["w"]]), "stay":set([w_event for w_event in rw_event["stay"]]), "ctrl":set([w_event for w_event in rw_event["ctrl"]])}
                if len(rw_event["stay"]) > 0:
                    prop_row[rw_event["r"]] = 1.0
                else:
                    mask_probs = [1.0 - prob for dst_reg, prob in set([w_event for w_event in rw_event["w"]] + [w_event for w_event in rw_event["ctrl"]])]
                    tot_m_probs = 1.0
                    for m_prob in mask_probs:
                        tot_m_probs *= m_prob
                    tot_p_probs = 1.0 - tot_m_probs
                    prop_row[rw_event["r"]] = tot_p_probs

            self.rw_table_list.append(rw_row)
            self.reg_prop_list.append(prop_row)


class AceAnalysis:
    def __init__(self, ace_dir:str, sigtable_dir:str):
        f = open(sigtable_dir,"r")
        self.sig_dict = json.load(f)
        f.close()

        self.last_cyc_er_id = {}
        self.reg_table = {}
        for reg in self.sig_dict["ff"]:
            self.reg_table[reg] = None
            self.last_cyc_er_id[reg] = None

        self.rw_loader = RWTableLoader(ace_dir)
        self.rw_loader.load()
        self.rw_table = self.rw_loader.rw_table_list
        self.tot_cyc = self.rw_loader.total_cycle
        self.start_cyc = self.rw_loader.start_cyc

        # A list of ER nodes for fault propagation graph.
        self.prop_graph_nodes = []
        self.prop_graph_links = []

        # A list of un-ACE interval nodes.
        self.unACE_int = []

    def prop_graph_construct(self):
        r_event_list = []
        for idx, row in enumerate(self.rw_table):
            # Create a new ER node
            self.create_new_er(idx)

            # Connect parent nodes to node being constructed
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
            
            # Complete ER nodes
            for reg in self.sig_dict["ff"]:
                rw_events = self.rw_table[idx]
                # W-event on the reg
                if reg not in rw_events:
                    self.unACE_int.append(self.reg_table[reg])
                    self.prop_graph_nodes.append(self.reg_table[reg])
                    self.reg_table[reg] = None
                # R-event on the reg
                elif len(rw_events[reg]["w"]) + len(rw_events[reg]["ctrl"]) > 0:
                    r_event_list.append(reg)
                    self.last_cyc_er_id[reg] = len(self.prop_graph_nodes)
                    self.prop_graph_nodes.append(self.reg_table[reg])
                    self.reg_table[reg] = None
                # ER
                else:
                    self.reg_table[reg].end = self.reg_table[reg].end + 1

    def create_new_er(self,idx):
        for reg in self.reg_table:
            if self.reg_table[reg] == None:
                self.reg_table[reg] = ERNode(reg_name = reg, start = (idx + self.start_cyc))

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument('--rw_table_dir', type=str, help='RW-table directory')
    parser.add_argument("--sig_list_dir", type=str, help="Logic value path")

    # Step 3: Parse the arguments
    args = parser.parse_args()

    rw_table_dir = args.rw_table_dir

    sig_list_dir = args.sig_list_dir

    ace = AceAnalysis(ace_dir=rw_table_dir, sigtable_dir=sig_list_dir)
    ace.prop_graph_construct()
