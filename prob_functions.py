from rtl_functions import *
from num_convert import *
from utils import * 


def f_prop(l_f_list:dict,r_f_list:dict):
    f_list = {}
    for fault, prob in l_f_list.items():
        f_list_append(fault,prob,f_list)
    for fault, prob in r_f_list.items():
        f_list_append(fault,prob,f_list)
    return f_list

def f_list_append(fault,prob,f_list:dict):
    if fault in f_list:
        if f_list[fault] < prob:
            f_list[fault] = prob
    else:
        f_list[fault] = prob

def prob_and(l_value,r_value,result):
    l_sen_num = r_value.count("1")
    r_sen_num = l_value.count("1")
    width = len(result)
    l_prob = float(l_sen_num)/float(width)
    r_prob = float(r_sen_num)/float(width)
    return l_prob, r_prob

def prob_or(l_value,r_value,result):
    l_sen_num = r_value.count("0")
    r_sen_num = l_value.count("0")
    width = len(result)
    l_prob = float(l_sen_num)/float(width)
    r_prob = float(r_sen_num)/float(width)
    return l_prob, r_prob

def prob_shiftl(l_value,r_value,result):
    if "x" in r_value:
        return 0.0, 0.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_shiftr(l_value,r_value,result):
    if "x" in r_value:
        return 0.0, 0.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_shiftrs(l_value,r_value,result):
    if "x" in r_value:
        return 0.0, 0.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_eq(l_value,r_value,result):
    if result == "1": # if is equal
        return 1.0, 1.0
    elif result == "x":
        return 0.0, 0.0
    else:
        l_xor_r = val_xor(l_value,r_value,len(r_value))
        diff_bit_num = l_xor_r.count("1")
        if diff_bit_num == 0:
            return 1.0, 1.0
        if diff_bit_num == 1:
            return 1.0/len(l_xor_r), 1.0/len(l_xor_r)
        else:
            return 1.0/diff_bit_num, 1.0/diff_bit_num

def prob_neq(l_value,r_value,result):
    if result == "x":
        return 0.0, 0.0
    elif result == "0": # if is equal
        return 1.0, 1.0
    else:
        l_xor_r = val_xor(l_value,r_value,len(l_value))
        diff_bit_num = l_xor_r.count("1")
        if diff_bit_num == 1:
            return 1.0/len(l_xor_r), 1.0/len(l_xor_r)
        else:
            return 1.0/diff_bit_num, 1.0/diff_bit_num

def prob_logand(l_value,r_value,result):
    if result == "x":
        return 0.0, 0.0
    elif "1" not in r_value+l_value:
        # l_value == 0, r_value == 0
        return 1.0, 1.0
    elif "1" not in r_value:
        # l_value != 0, r_value == 0
        return 0.0, 1.0
    elif "1" not in l_value:
        # l_value == 0, r_value != 0
        return 1.0, 0.0
    else:
        # l_value != 0, r_value != 0
        return 0.5**l_value.count("1"), 0.5**r_value.count("1")

def prob_logor(l_value,r_value,result):
    if result == "x":
        return 0.0, 0.0
    elif "1" not in r_value+l_value:
        # l_value == 0, r_value == 0
        return 1.0, 1.0
    elif "1" not in r_value:
        # l_value != 0, r_value == 0
        return float(l_value.count("1"))/float(len(l_value)), 0.0
    elif "1" not in l_value:
        # l_value == 0, r_value != 0
        return 0.0, float(r_value.count("1"))/float(len(r_value))
    else:
        # l_value != 0, r_value != 0
        return 0.0, 0.0

def prob_gt(l_value,r_value,result):
    l_width = len(l_value)
    r_width = len(r_value)
    l_max = 2**l_width - 1
    r_max = 2**r_width - 1
    if result == "x":
        return 0.0, 0.0
    elif result == "1":
        # lv > rv
        # lv -> (lv <= rv)
        l_prob = float(int(r_value,2))/float(l_max)
        # rv -> (lv <= rv)
        r_top = max(int(l_value,2),r_max)
        r_prob = float(abs(r_top - int(l_value,2)))/float(r_max)
    else:
        # lv <= rv
        # lv -> (lv > rv)
        l_top = max(int(r_value,2),l_max)
        l_prob = float(abs(l_top - int(r_value,2)))/float(l_max)
        # rv -> (lv > rv)
        r_prob = float(int(l_value,2))/float(r_max)
    return l_prob, r_prob

def prob_gte(l_value,r_value,result):
    l_width = len(l_value)
    r_width = len(r_value)
    l_max = 2**l_width - 1
    r_max = 2**r_width - 1
    if result == "x":
        return 0.0, 0.0
    elif result == "1":
        # lv >= rv
        # lv -> (lv < rv)
        l_prob = float(int(r_value,2))/float(l_max)
        # rv -> (lv <= rv)
        r_top = max(int(l_value,2),r_max)
        r_prob = float(abs(r_top - int(l_value,2)))/float(r_max)
    else:
        # lv < rv
        # lv -> (lv >= rv)
        l_top = max(int(r_value,2),l_max)
        l_prob = float(abs(l_top - int(r_value,2)))/float(l_max)
        # rv -> (lv > rv)
        r_prob = float(int(l_value,2))/float(r_max)
    return l_prob, r_prob

def prob_lte(l_value,r_value,result):
    l_width = len(l_value)
    r_width = len(r_value)
    l_max = 2**l_width - 1
    r_max = 2**r_width - 1
    if result == "x":
        return 0.0, 0.0
    elif result == "0":
        # lv > rv
        # lv -> (lv <= rv)
        l_prob = float(int(r_value,2))/float(l_max)
        # rv -> (lv <= rv)
        r_top = max(int(l_value,2),r_max)
        r_prob = float(abs(r_top - int(l_value,2)))/float(r_max)
    else:
        # lv <= rv
        # lv -> (lv > rv)
        l_top = max(int(r_value,2),l_max)
        l_prob = float(abs(l_top - int(r_value,2)))/float(l_max)
        # rv -> (lv > rv)
        r_prob = float(int(l_value,2))/float(r_max)
    return l_prob, r_prob

def prob_lt(l_value,r_value,result):
    l_width = len(l_value)
    r_width = len(r_value)
    l_max = 2**l_width - 1
    r_max = 2**r_width - 1
    if result == "x":
        return 0.0, 0.0
    elif result == "0":
        # lv >= rv
        # lv -> (lv < rv)
        l_prob = float(int(r_value,2))/float(l_max)
        # rv -> (lv <= rv)
        r_top = max(int(l_value,2),r_max)
        r_prob = float(abs(r_top - int(l_value,2)))/float(r_max)
    else:
        # lv < rv
        # lv -> (lv >= rv)
        l_top = max(int(r_value,2),l_max)
        l_prob = float(abs(l_top - int(r_value,2)))/float(l_max)
        # rv -> (lv > rv)
        r_prob = float(int(l_value,2))/float(r_max)
    return l_prob, r_prob

def prob_lts(l_value,r_value,result):
    l_width = len(l_value)
    l_max = 2**(l_width-1) - 1
    l_min = -2**(l_width-1)
    r_width = len(r_value)
    r_max = 2**(r_width-1) - 1
    r_min = -2**(r_width-1)
    if "x" in l_value+r_value:
        return 0.0, 0.0
    else:
        l_int = bin_2_signed_int(l_value)
        r_int = bin_2_signed_int(r_value)
        if l_int < r_int:
            l_top = max(l_max, r_int)
            l_prob = float(abs(l_top - r_int))/float(2**l_width)
            r_bot = min(r_min, l_int)
            r_prob = float(abs(l_int - r_bot))/float(2**r_width)
        else:
            l_bot = min(l_min, r_int)
            l_prob = float(abs(r_int - l_bot))/float(2**l_width)
            r_top = max(r_max, l_int)
            r_prob = float(abs(r_top - l_int))/float(2**r_width)
        return l_prob, r_prob

def prob_2_op(node):
    result = node.ivalue
    l_value = node.children[0].ivalue
    r_value = node.children[1].ivalue
    if node.tag == "and":
        return prob_and(l_value,r_value,result)
    elif node.tag == "or":
        return prob_or(l_value,r_value,result)
    elif node.tag == "xor":
        return 1.0, 1.0
    elif node.tag == "add":
        return 1.0, 1.0
    elif node.tag == "sub":
        return 1.0, 1.0
    elif node.tag == "muls":
        return 1.0, 1.0
    elif node.tag == "shiftl":
        return prob_shiftl(l_value,r_value,result)
    elif node.tag == "shiftr":
        return prob_shiftr(l_value,r_value,result)
    elif node.tag == "shiftrs":
        return prob_shiftrs(l_value,r_value,result)
    elif node.tag == "eq":
        return prob_eq(l_value,r_value,result)
    elif node.tag == "neq":
        return prob_neq(l_value,r_value,result)
    elif node.tag == "gt":
        return prob_gt(l_value,r_value,result)
    elif node.tag == "gte":
        return prob_gte(l_value,r_value,result)
    elif node.tag == "lte":
        return prob_lte(l_value,r_value,result)
    elif node.tag == "lt":
        return prob_lt(l_value,r_value,result)
    elif node.tag == "lts":
        return prob_lts(l_value,r_value,result)
    elif node.tag == "concat":
        return 1.0, 1.0
    elif node.tag == "logand":
        return prob_logand(l_value,r_value,result)
    elif node.tag == "logor":
        return prob_logor(l_value,r_value,result)
    elif node.tag == "replicate":
        return 1.0, 1.0
    else:
        raise SimulationError(f"Unknown 2 ports op to calculate probability: tag = {node.tag}.",7)
    return 1.0, 1.0


def prob_redor(i_value,result):
    if result == "x":
        return 0.0
    elif result == "0":
        return 1.0
    else:
        # only one 1 bit
        # multiple 1 bits
        return 0.5**len(i_value)

def prob_redand(i_value,result):
    if result == "x":
        return 0.0
    elif result == "1":
        return 1.0
    else:
        # multiple 0 bits
        return 0.5**len(i_value)

def prob_1_op(node):
    result = node.ivalue
    i_value = node.children[0].ivalue
    if node.tag == "not":
        return 1.0
    elif node.tag == "extends":
        return 1.0
    elif node.tag == "extend":
        return 1.0
    elif node.tag == "redor":
        return prob_redor(i_value,result)
    elif node.tag == "redand":
        return prob_redand(i_value,result)
    elif node.tag == "negate":
        return 1.0
    else:
        raise SimulationError(f"Unknown 1 port op to calculate probability: tag = {node.tag}.",8)
    
