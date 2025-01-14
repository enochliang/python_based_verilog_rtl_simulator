from rtl_functions import *
from num_convert import *


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
        return 1.0, 1.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_shiftr(l_value,r_value,result):
    if "x" in r_value:
        return 1.0, 1.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_shiftrs(l_value,r_value,result):
    if "x" in r_value:
        return 1.0, 1.0
    else:
        offset = bin_2_signed_int(r_value)
        width = len(result)
        return float(offset - width)/float(width), 1.0

def prob_eq(l_value,r_value,result):
    if result == "1": # if is equal
        return 1.0, 1.0
    else:
        l_xor_r = val_xor(l_value,r_value,len(r_value))
        diff_bit_num = l_xor_r.count("1")
        if diff_bit_num == 0:
            return 1.0, 1.0
        if diff_bit_num == 1:
            return 1.0/len(l_xor_r), 1.0/len(l_xor_r)
        else: #TODO
            return 1.0/diff_bit_num, 1.0/diff_bit_num

def prob_neq(l_value,r_value,result):
    if result == "0": # if is equal
        return 1.0, 1.0
    else:
        l_xor_r = val_xor(l_value,r_value,len(l_value))
        diff_bit_num = l_xor_r.count("1")
        if diff_bit_num == 1:
            return 1.0/len(l_xor_r), 1.0/len(l_xor_r)
        else: #TODO
            return 1.0/diff_bit_num, 1.0/diff_bit_num


def prob_logand(l_value,r_value,result):
    if result == "1":
        return 1.0, 1.0
    else:
        #TODO
        return 1.0, 1.0

def prob_logor(l_value,r_value,result):
    if result == "0":
        return 1.0, 1.0
    else:
        #TODO
        return 1.0, 1.0



def prob_2_op(node):
    result = node.value
    l_value = node.children[0].value
    l_faultlist = node.children[0].fault_list
    r_value = node.children[1].value
    r_faultlist = node.children[1].fault_list
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
        #return prob_gt(l_value,r_value,result)
        return 1.0, 1.0
    elif node.tag == "gte":
        #return prob_gte(l_value,r_value,result)
        return 1.0, 1.0
    elif node.tag == "lte":
        #return prob_lte(l_value,r_value,result)
        return 1.0, 1.0
    elif node.tag == "lt":
        #return prob_lt(l_value,r_value,result)
        return 1.0, 1.0
    elif node.tag == "lts":
        #return prob_lts(l_value,r_value,result)
        return 1.0, 1.0
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


def prob_1_op(node):
    if node.tag == "not":
        return 1.0
    elif node.tag == "extends":
        return 1.0
    elif node.tag == "extend":
        return 1.0
    elif node.tag == "redor":
        #return prob_redor(i_value,result)
        return 1.0
    elif node.tag == "redand":
        #return prob_redand(i_value,result)
        return 1.0
    elif node.tag == "negate":
        return 1.0
    else:
        raise SimulationError(f"Unknown 1 port op to calculate probability: tag = {node.tag}.",8)
    
