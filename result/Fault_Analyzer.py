import pandas as pd
import ast



class stat_reg_level_fault:
    def __init__(self):
        self.fault_effect = pd.read_csv("fault_sim_result.csv")
        self.rw_table = pd.read_csv("prob_rw_table.csv")

        self.rw_table_list = list()
        for idx , row in self.rw_table.iterrows():
            cyc = row["cycle"]
            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            rw_row = {}
            for rw_event in rw_events:
                rw_row[rw_event["r"]] = set([w_event[0] for w_event in rw_event["w"]])
            self.rw_table_list.append(rw_row)

    def stat(self):
        for i, fault_case in self.fault_effect.iterrows():
            if len(ast.literal_eval(fault_case["dst_bit"])) == 1 and ast.literal_eval(fault_case["dst_bit"])[0] == fault_case["src_bit"]:
                continue
            src_reg = fault_case["src_bit"].split("[")[0]
            dst_regs = ast.literal_eval(fault_case["dst_bit"])
            cyc = fault_case["cycle"]
        
            dst_regs = set([dst_reg.split("[")[0] for dst_reg in dst_regs if dst_reg != fault_case["src_bit"]])
            if src_reg in self.rw_table_list[cyc]: # 
                flag = False
                for dst_reg in dst_regs:
                    if not dst_reg in self.rw_table_list[cyc][src_reg]:
                        print(f"fsim: src_reg = {src_reg}, dst_regs = {dst_regs}")
                        print(f"algo: rw_table_list[cyc][src_reg] = {rw_table_list[cyc][src_reg]}")
                        flag = True
                if flag:
                    if len(ast.literal_eval(fault_case["dst_bit"])) == 1 and ast.literal_eval(fault_case["dst_bit"])[0] == fault_case["src_bit"]:
                        pass
                    else:
                        print(fault_case["cycle"],fault_case["src_bit"],"->",fault_case["dst_bit"],f"fault_effect = {fault_case['fault_effect']}")
                    print("=====")
            else:
                if fault_case['fault_effect'] != "masked":
                    print("Read-Event Doesn't exist")
                    print(fault_case["cycle"],fault_case["src_bit"],"->",fault_case["dst_bit"],f"fault_effect = {fault_case['fault_effect']}")

    def count_link_prob(self):
        probs = []
        for idx , row in self.rw_table.iterrows():
            rw_events = row["rw_event"]
            rw_events = ast.literal_eval(rw_events)
            for rw_event in rw_events:
                for w_event in rw_event["w"]:
                    probs.append(w_event[1])

        distrib = {}
        for prob in probs:
            if prob in distrib:
                distrib[prob] += 1
            else:
                distrib[prob] = 1
        print(len(probs))
        print(distrib)



class stat_bit_level_fault:
    def __init__(self):
        self.fault_effect = pd.read_csv("fault_sim_result.csv")

    def stat(self):
        stat = {}
        for i, fault_case in self.fault_effect.iterrows():
            if not fault_case['fault_effect'] in stat:
                stat[fault_case['fault_effect']] = 1
            else:
                stat[fault_case['fault_effect']] += 1
            if fault_case['fault_effect'] == "single":
                if fault_case['src_bit'] == ast.literal_eval(fault_case['dst_bit'])[0]:
                    if "staying" in stat:
                        stat["staying"] += 1
                    else:
                        stat["staying"] = 1
        print(stat)


analyzer = stat_reg_level_fault()
analyzer.count_link_prob()
