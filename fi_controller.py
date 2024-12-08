import os
import pandas as pd
import json

class SimulationError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"{self.args[0]} (Error Code: {self.error_code})"

class GenFaultList:
    def __init__(self,cycle:int,_sig_dict:dict):
        self.total_cyc = cycle
        self.sig_dict = _sig_dict
        self.idx_2_sig_name_map = {}
        for idx,sig_name in enumerate(self.sig_dict["ff"]):
            self.idx_2_sig_name_map[str(idx)] = sig_name
    def _get_fault_list(self):
        self.all_fault_list = []
        for cyc in range(self.total_cyc):
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                width = self.sig_dict["ff"][sig_name]
                for bit in range(width):
                    self.all_fault_list.append((cyc,idx,bit))

    def setup(self):
        self._get_fault_list()

    def run_fault_sim(self):
        for fi_case in self.all_fault_list:
            f = open("control.txt","w")
            f.write(f"{fi_case[0]}\n{fi_case[1]}\n{fi_case[2]}")
            f.close()
            os.system("./Vfi_tb_sha1")

    def result_stat(self):
        clock_cyc_col = []
        src_bit_col = []
        dst_bit_col = []
        faulty_effect_class_col = []
        
        for fi_case in self.all_fault_list:
            f = open(f"result/Result_C{fi_case[0]:05}_R{fi_case[1]:03}_B{fi_case[2]:03}.txt","r")
            faulty_values = f.read().split("\n")
            f.close()
            src_reg_name = self.idx_2_sig_name_map[str(fi_case[1])]
            dst_reg_list = []
            for idx,sig_name in enumerate(self.sig_dict["ff"]):
                if len(faulty_values[idx]) != int(self.sig_dict["ff"][sig_name]):
                    raise SimulationError("Error: Width Not Match.",1)
                else:
                    for c_idx in range(len(faulty_values[idx])):
                        if faulty_values[idx][len(faulty_values[idx])-1-c_idx] == "1":
                            dst_reg_list.append(f"{sig_name}[{c_idx}]")
            clock_cyc_col.append(fi_case[0])
            src_bit_col.append(f"{src_reg_name}[{fi_case[2]}]")
            dst_bit_col.append(dst_reg_list)
            if dst_reg_list == []:
                faulty_effect_class_col.append("masked")
            elif len(dst_reg_list) == 1:
                faulty_effect_class_col.append("single")
            else:
                faulty_effect_class_col.append("multiple")

        df = pd.DataFrame({"cycle":clock_cyc_col,"src_bit":src_bit_col,"dst_bit":dst_bit_col,"fault_effect":faulty_effect_class_col})
        df.to_csv("fault_sim_result.csv")

                            

if __name__ == "__main__":

    f = open("sig_dict.json","r")
    sig_dict = json.load(f)
    f.close()
    fl = GenFaultList(1037,sig_dict)
    fl.setup()
    #fl.run_fault_sim()
    fl.result_stat()
