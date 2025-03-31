import pandas as pd
import ast
import re
import json

def rw_table(rw_table_file:str):
    """
    Loads the RW table from CSV and processes it into a list of RW events and propagation probabilities.

    The CSV is expected to have columns 'cycle' and 'rw_event', where 'rw_event' is a string representation
    of a list of dictionaries containing read ('r'), write ('w'), stay ('stay'), and control ('ctrl') events.
    """

    """
    rw_table_list = [{"src_a":{}, "src_b":{}},    |- cycle
                     {"src_a":{}, "src_b":{}},    |
                     {"src_a":{}, "src_b":{}},    |
                     ...]                         |
    reg_prop_list = [{"src_a":prob, "src_b":prob},    |- cycle
                     {"src_a":prob, "src_b":prob},    |
                     {"src_a":prob, "src_b":prob},    |
                     ...]
    """
    rw_table = pd.read_csv(rw_table_file)
    total_cycle = len(rw_table)
    start_cyc = rw_table.iloc[0]['cycle']
    # output
    rw_table_list = list()
    reg_prop_list = list()

    for idx, row in rw_table.iterrows():
        rw_events = row["rw_event"]
        rw_events = ast.literal_eval(rw_events)
        rw_row = {}
        prop_row = {}
        for rw_event in rw_events:
            src_reg = re.sub(r'\bgenblk\d+\.', '', rw_event["r"])
            dst_regs_w = set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["w"]])
            dst_reg_s  = set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["stay"]])
            dst_regs_c = set([(re.sub(r'\bgenblk\d+\.', '', w_event[0]),w_event[1]) for w_event in rw_event["ctrl"]])
            rw_row[src_reg] = {"w": dst_regs_w, "stay": dst_reg_s, "ctrl": dst_regs_c}
            
            mask_probs = [1.0 - prob for dst_reg, prob in list(dst_regs_w | dst_regs_c)]
            tot_m_probs = 1.0
            for m_prob in mask_probs:
                tot_m_probs *= m_prob
            tot_p_probs = 1.0 - tot_m_probs

            if len(rw_event["stay"]) > 0:
                if len(mask_probs) == 0:
                    prop_row[rw_event["r"]] = 0.0
                else:
                    prop_row[rw_event["r"]] = tot_p_probs
            else:
                prop_row[rw_event["r"]] = tot_p_probs

        rw_table_list.append(rw_row)
        reg_prop_list.append(prop_row)

    output = {"start_cyc":start_cyc,
              "total_cyc":total_cycle,
              "rw_table_list":rw_table_list,
              "reg_prop_list":reg_prop_list
             }
    print(f"[RW-Table Loaded]: <{rw_table_file}>")
    return output


def sig_dict(sigtable_dir):
    f = open(sigtable_dir, "r")
    sig_dict = json.load(f)
    f.close()
    print(f"[Signal-Table Loaded]: <{sigtable_dir}>")
    return sig_dict
