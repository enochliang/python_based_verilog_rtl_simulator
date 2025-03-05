import os
import pandas as pd
import json
import ast
from tqdm import tqdm
import argparse

class RTLFSimulationError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"

class GenFaultList:
    def __init__(self,sigtable_dir:str, ace_dir:str):

        f = open(sigtable_dir,"r")
        self.sig_dict = json.load(f)
        f.close()

        self.idx_2_sig_name_map = {}
        self.sig_name_2_idx_map = {}
        self.total_cyc = 0
        self.start_cyc = 0
        self.rw_table = None
        self.rw_table_list = None

        for idx,sig_name in enumerate(self.sig_dict["ff"]):
            self.idx_2_sig_name_map[str(idx)] = sig_name
            self.sig_name_2_idx_map[sig_name] = idx

        self.rw_table_file = ace_dir
        
        self.load_rw_table()

    def load_rw_table(self):
        self.rw_table = pd.read_csv(self.rw_table_file)
        self.rw_table_list = list()
        self.total_cyc = len(self.rw_table)
        for idx , row in self.rw_table.iterrows():
            cyc = row["cycle"]
            if idx == 0:
                self.start_cyc = cyc
            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            rw_row = {}
            for rw_event in rw_events:
                rw_row[rw_event["r"]] = {"w":set([w_event for w_event in rw_event["w"]]), "stay":set([w_event for w_event in rw_event["stay"]]), "ctrl":set([w_event for w_event in rw_event["ctrl"]])}
            self.rw_table_list.append(rw_row)


        print("rw table loaded")
    

    def _get_all_fault_list(self):
        self.all_fault_list = []
        for cyc in range(self.start_cyc, self.start_cyc+self.total_cyc ):
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                width = self.sig_dict["ff"][sig_name]
                for bit in range(width):
                    self.all_fault_list.append( (cyc, idx, bit) )

    def _get_ace_fault_list(self):
        self.data_fault_list = []
        self.ctrl_fault_list = []
        for cyc, rw_row in enumerate(self.rw_table_list):
            for r_event in rw_row:
                if len(rw_row[r_event]["ctrl"]) > 0:
                    width = self.sig_dict["ff"][r_event]
                    idx = self.sig_name_2_idx_map[r_event]
                    for bit in range(width):
                        self.ctrl_fault_list.append( (cyc+self.start_cyc, idx, bit) )
                    continue

                if len(rw_row[r_event]["w"]) == 0:
                    continue
                width = self.sig_dict["ff"][r_event]
                idx = self.sig_name_2_idx_map[r_event]
                for bit in range(width):
                    self.data_fault_list.append( (cyc+self.start_cyc, idx, bit) )
        print(f"ace fault list obtained")
        print(f"total data fault injection = {len(self.data_fault_list)}")
        print(f"total ctrl fault injection = {len(self.ctrl_fault_list)}")

    def setup(self):
        #self._get_all_fault_list()
        self._get_ace_fault_list()


class FaultInjection(GenFaultList):
    def __init__(self,sigtable_dir:str, hw_dir:str, ace_dir:str, fi_name:str="fi_sim_veri"):
        GenFaultList.__init__(self,sigtable_dir,ace_dir)
        self.hw_dir = hw_dir
        self.fi_name = fi_name
        self.fsim_exe_file = f"{self.fi_name} > fsim.log"

    def run_all_fault_sim(self):

        self._get_all_fault_list()

        for fi_case in self.all_fault_list:
            f = open(self.hw_dir+"/control.txt","w")
            f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
            f.close()
            os.system(self.fsim_exe_file)
        
        self.result_stat(mode="total")

#    def reg_level_dataframe(self):
#        reg_level_fault_effect = [{}]*(self.total_cyc)


    def run_data_fault_sim(self):

        self._get_ace_fault_list()

        tot = len(self.data_fault_list)
        cnt = 0
        
        print("[Progress] running fault injection...")
        with tqdm(total=tot) as pbar:
            for fi_case in self.data_fault_list:
                f = open(self.hw_dir+"/control.txt","w")
                f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
                f.close()
                os.system(self.fsim_exe_file)
                cnt += 1
                if cnt % 100 == 0:
                    pbar.update(100)
        print("fault injection done.")

        self.result_stat(mode="data")

    def run_ctrl_fault_sim(self):

        self._get_ace_fault_list()

        tot = len(self.ctrl_fault_list)
        cnt = 0
        
        print("[Progress] running fault injection...")
        with tqdm(total=tot) as pbar:
            for fi_case in self.ctrl_fault_list:
                f = open(self.hw_dir+"/control.txt","w")
                f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
                f.close()
                os.system(self.fsim_exe_file)
                cnt += 1
                if cnt % 100 == 0:
                    pbar.update(100)
        print("fault injection done.")

        self.result_stat(mode="ctrl")

    def result_stat(self, mode:str):
        clock_cyc_col = []
        src_bit_col = []
        dst_bit_col = []
        faulty_effect_class_col = []

        #reg_level_fault_effect = {}
        
        print("[Progress] observing fault injection result...")

        if mode == "data":
            tot = len(self.data_fault_list)
            fault_list = self.data_fault_list
        elif mode == "ctrl":
            tot = len(self.ctrl_fault_list)
            fault_list = self.ctrl_fault_list
        elif mode == "total":
            tot = len(self.all_fault_list)
            fault_list = self.all_fault_list
        cnt = 0
        with tqdm(total=tot) as pbar:
            for fi_case in fault_list:
                # Read faulty bit
                f = open(f"{self.hw_dir}/result/result_C{fi_case[0]:07}_R{fi_case[1]:04}_B{fi_case[2]:04}.txt","r")
                faulty_values = f.read().split("\n")
                f.close()
                # Read golden value for unknown elimination
                f = open(f"{self.hw_dir}/golden_value/golden_value_C{fi_case[0]+1:07}.txt")
                golden_values = f.read().split("\n")
                f.close()

                src_reg_name = self.idx_2_sig_name_map[str(fi_case[1])]
                cycle = fi_case[0]
                dst_reg_list = []


                for idx,sig_name in enumerate(self.sig_dict["ff"]):
                    width = len(faulty_values[idx])
                    if len(faulty_values[idx]) != int(self.sig_dict["ff"][sig_name]):
                        raise RTLFSimulationError("Error: Width Not Match.",1)
                    else:
                        #prop_flag = False
                        for c_idx in range(width):
                            if golden_values[idx][width-1-c_idx] == "x":
                                continue
                            if faulty_values[idx][width-1-c_idx] == "1":
                                #prop_flag = True
                                dst_reg_list.append(f"{sig_name}[{c_idx}]")
                    #if prop_flag:
                    #    if (cycle, src_reg_name) in reg_level_fault_effect:
                    #        reg_level_fault_effect[cycle-self.start_cyc][src_reg_name][sig_name] += 1
                    #    else:
                    #        reg_level_fault_effect[cycle-self.start_cyc][src_reg_name] = {}
                    #        reg_level_fault_effect[cycle-self.start_cyc][src_reg_name][sig_name] = 1


                clock_cyc_col.append(cycle)
                src_bit_col.append(f"{src_reg_name}[{fi_case[2]}]")
                dst_bit_col.append(dst_reg_list)
                if dst_reg_list == []:
                    faulty_effect_class_col.append("masked")
                elif len(dst_reg_list) == 1:
                    faulty_effect_class_col.append("single")
                else:
                    faulty_effect_class_col.append("multiple")


                cnt += 1
                if cnt % 100 == 0:
                    pbar.update(100)


        df = pd.DataFrame({"cycle":clock_cyc_col,"src_bit":src_bit_col,"dst_bit":dst_bit_col,"fault_effect":faulty_effect_class_col})
        df.to_csv(f"fault_sim_result({mode}).csv")


                            

if __name__ == "__main__":
    # Step 1: Create the parser
    parser = argparse.ArgumentParser(description="A simple example of argparse usage.")

    # Step 2: Define arguments
    parser.add_argument("-m",'--mode', type=str, help="fault injection mode [total, data, ctrl]")
    parser.add_argument("-t",'--rwtable_dir', type=str, help="rw-table directory")
    parser.add_argument("-d",'--hw_dir', type=str, help="hardware directory")
    parser.add_argument("-f", "--fi_name", type=str, help="fault simulator directory")                  # Positional argument
    parser.add_argument("-s", "--sigtable_dir", type=str, help="signal table directory")

    # Step 3: Parse the arguments
    args = parser.parse_args()

    inj = FaultInjection(
              sigtable_dir = args.sigtable_dir, 
              hw_dir = args.hw_dir, 
              ace_dir = args.rwtable_dir, 
              fi_name = args.fi_name
          )

    if args.mode == "total":
        inj.run_total_fault_sim()
    elif args.mode == "data":
        inj.run_data_fault_sim()
    elif args.mode == "ctrl":
        inj.run_ctrl_fault_sim()
    #gen = GenFaultList(sig_dict)
    #gen.setup()
