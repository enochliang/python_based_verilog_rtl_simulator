from abc import ABC, abstractmethod

class Verilog_AST_Base_Node:
    def __init__(self):
        self._tag = ""
        self._children = []
        self.attrib = dict()
        self._ast_tree = None

    @property
    def children(self):
        return self._children

    @abstractmethod
    def tag(self):
        pass

    def _set_tree(self,tree):
        self._ast_tree = tree

    def get_tree(self):
        return self._ast_tree

    def append(self, node):
        node._set_tree(self._ast_tree)
        self._children.append(node)

class Verilog_AST_Node(Verilog_AST_Base_Node):
    def __init__(self):
        Verilog_AST_Base_Node.__init__(self)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self,tag:str):
        self._tag = tag

class Verilog_AST_Assign_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)
        self._tag = "assign"

    @property
    def rv_node(self):
        return self._children[0]

    @property
    def lv_node(self):
        return self._children[1]


class Verilog_AST_Control_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)

    @property
    def ctrl_node(self):
        if len(self._children) < 1:
            return None
        else:
            return self._children[0]

class Verilog_AST_IF_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "if"

    @property
    def true_id(self):
        if len(self._children) < 2:
            return None
        else:
            return self._children[1]

    @property
    def false_id(self):
        if len(self._children) < 3:
            return None
        else:
            return self._children[2]

class Verilog_AST_CASE_Node(Verilog_AST_Control_Node):
    def __init__(self):
        Verilog_AST_Control_Node.__init__(self)
        self._tag = "case"

    @property
    def caseitems(self):
        if len(self._children) <= 1:
            return []
        else:
            return [ self._ast_tree.nodes[node_id] for node_id in self._children[1:]]

class Verilog_AST_CASEITEM_Node(Verilog_AST_Node):
    def __init__(self):
        Verilog_AST_Node.__init__(self)
        self._tag = "caseitem"
        self.code_start_pos = 0

    @property
    def other_children(self):
        if len(self._children) == self.condition_end_pos:
            return []
        else:
            return self._children[self.code_start_pos:]

    @property
    def conditions(self):
        return self._children[:self.code_start_pos]

    def append(self, node):
        node._set_tree(self._ast_tree)
        if isinstance(node, Verilog_AST_Circuit_Node):
            self.code_start_pos += 1
        self._children.append(node)

class Verilog_AST_Circuit_Node(Verilog_AST_Node):
    def __init__(self,width=None):
        Verilog_AST_Node.__init__(self)
        self._width = width
        if width == None:
            self._value = None
        else:
            self._value = "x"*self._width
        self._signed = False

    @property
    def signed(self):
        return self._signed

    @signed.setter
    def signed(self,value:bool):
        self._signed = value

    @property
    def width(self):
        return self._width

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self,value:str):
        if len(value) == self._width:
            self._value = value
        else:
            raise Verilog_AST_Construction_Exception("value and width doesn't match.",0)

class Verilog_AST_Var_Node(Verilog_AST_Circuit_Node):
    def __init__(self,width:int):
        Verilog_AST_Circuit_Node.__init__(self,width)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self,value:str):
        self.__name = value

class Verilog_AST_Varref_Node(Verilog_AST_Circuit_Node):
    def __init__(self,width:int):
        Verilog_AST_Circuit_Node.__init__(self,width)
        self._tag = "varref"

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self,value:str):
        self.__name = value

    @property
    def ref_node(self):
        return self.__ref_node

    @ref_node.setter
    def ref_node(self,node):
        self.__ref_node = node

