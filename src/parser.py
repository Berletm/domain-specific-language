from typing import List, Tuple

import sys
import pymorphy3

def read_queries(pth: str) -> List[str]:
    queries = []
    
    with open(pth, "r") as f:
        lines = f.readlines()
        for l in lines :
            queries.append(l.strip("\n"))
    
    return queries

class Token:
    def __init__(self, token: str, pos: str=""):
        self.tok: str = token
        self.pos: str = pos
    
    def __repr__(self):
        return self.tok

def tokenize(query: str) -> List[Token]:
    
    def is_number(s:str):
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    words = query.split()
    
    morph = pymorphy3.MorphAnalyzer(lang="ru")
    tokens = []
    
    for w in words:
        if w[-1] == ",":
            w_ = w.strip(",")
            pos = morph.parse(w_)[0].tag.POS
            tokens.append(Token(w_, pos))
            tokens.append(Token(",", "PNCT"))
        else:
            pos = morph.parse(w)[0].tag.POS
            pos = "NUMR" if is_number(w) else pos
            tokens.append(Token(w, pos))
    
    return tokens

    
class Node:
    def __init__(self, token: Token, rule: str="", children:List=[]) -> None:
        self.val:Token     = token
        self.rule:str      = rule
        self.children:List = children
        
           
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos    = 0
        
    def current(self) -> Token|None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def eat(self) -> Token|None:
        token = self.current()
        self.pos += 1
        return token
    
    def expect(self, value: str):
        if self.current() and self.current().tok == value:
            return self.eat()
        raise SyntaxError("\n" + self.print_pos() + f"Expected {value} got {self.current()}")
    
    def print_pos(self) -> str:
        end_idx = min(self.pos, len(self.tokens))
        
        l = sum([len(tok.tok) for tok in self.tokens[:end_idx]])
        
        text = " ".join([tok.tok for tok in self.tokens])
        
        return text + "\n" + " " * (l + self.pos) + "^"*len(self.tokens[self.pos].tok) + "\n"
    
    def parse(self) -> Node:
        select_node  = self.parse_select()
        columns_node = self.parse_columns()
        source_node  = self.parse_source()
        conditions_node = self.parse_conditions()
        sort_node    = self.parse_sort_operator()
        limit_node   = self.parse_limit_operator()
        
        if self.pos != len(self.tokens):
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected trailing tokens [{self.tokens[self.pos:]}]")
        
        return Node(Token("query"), "root", children=[select_node, columns_node, source_node, conditions_node, sort_node, limit_node])
        
    def parse_select(self) -> Node:
        tok = self.current()
        
        keywords = ["выбрать", "достать", "выдать", "взять"]
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.tok not in keywords:
            raise SyntaxError("\n" + self.print_pos() + f"Expected {keywords}, got {tok}")
        
        self.eat()
        return Node(tok, "select-operator")
    
    def parse_columns(self) -> Node:
        tok = self.current()
        
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        
        if tok.tok in ["всё", "все"]:
            self.eat()
            return Node(tok, "all")
        else:
            return self.parse_column_list()

    def parse_column_list(self) -> Node:
        first_column = self.parse_column()
        rest_columns = self.parse_column_list_tail()
        
        return Node(Token(""), "column-list", [first_column, rest_columns])
    
    def parse_column(self) -> Node:
        tok = self.current()
        
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.pos != "NOUN":
            raise SyntaxError("\n" + self.print_pos() + f"Expected NOUN token got {tok} token with pos {tok.pos}.")
        
        self.eat()
        return Node(tok, "column")

    def parse_column_list_tail(self) -> Node:
        tok = self.current()
        
        if tok is None:
            return Node(Token("epsilon"), "column-list-tail", [])
        
        if tok.tok == ",":
            self.eat()
            comma = Node(tok, "comma")
            
            column = self.parse_column()
            tail = self.parse_column_list_tail()
            
            return Node(Token(""), "column-list-tail", [comma, column, tail])
        else:
            return Node(Token("epsilon"), "column-list-tail", [])
    
    def parse_source(self) -> Node:
        from_tok  = self.expect("из")
        from_node = Node(from_tok, "from") 
        
        table_tok = self.expect("таблицы")
        table_node = Node(table_tok, "table")
        
        from_table_node = Node(Token(""), "from-table", [from_node, table_node])
        
        noun_tok = self.current()
        if noun_tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {noun_tok} token.")
        elif noun_tok.pos != "NOUN":
            raise SyntaxError("\n" + self.print_pos() + f"Expected NOUN token got {noun_tok} token with pos {noun_tok.pos}.")
        
        noun_node = Node(noun_tok, "noun")
        
        self.eat()
        return Node(Token(""), "source", [from_table_node, noun_node])
    
    def parse_conditions(self) -> Node:
        tok = self.current()
        
        if tok.tok == "где":
            where_tok = self.expect("где")
            where_node = Node(where_tok, "where")
        
            cond_node = self.parse_condition()
            return Node(Token(""), "conditions", [where_node, cond_node])
        else:
            return Node(Token("epsilon"), "conditions")
    
    def parse_condition(self) -> Node:
        left_expr_node = self.parse_expression()
        
        tail = self.parse_expression_tail()
        
        return Node(Token(""), "condition", [left_expr_node, tail])
    
    def parse_expression(self) -> Node:
        tok = self.current()
        
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.pos not in ["NOUN", "ADJS"]:
            raise SyntaxError("\n" + self.print_pos() + f"Expected NOUN token got {tok} token with pos {tok.pos}.")
        
        noun_node = Node(tok, tok.pos.lower())
        self.eat()
        
        sign_node = self.parse_inequality_signs()
 
        condition_node = self.parse_condition_word()
        
        return Node(Token(""), "expression", [noun_node, sign_node, condition_node])
    
    def parse_expression_tail(self) -> Node:
        tok = self.current()
        
        if tok is not None and tok.tok in ["и", "или"]:
            chain_node = self.parse_chain()
            expr_node  = self.parse_expression()
            return Node(Token(""), "expression-tail", [chain_node, expr_node])
        
        return Node(Token("epsilon"), "expression-tail")
    
    def parse_chain(self) -> Node:
        tok = self.current()
        
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.tok not in ["и", "или"]:
            raise SyntaxError("\n" + self.print_pos() + f"Expected NOUN token got {tok} token with pos {tok.pos}.")

        self.eat()
        return Node(tok, "chain")
    
    def parse_inequality_signs(self) -> Node:
        tok = self.current()

        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.pos == "COMP":
            self.eat()
            return Node(tok, "inequality-signs")
        elif tok.tok not in ["<", ">", "==", "!=", ">=", "<="]:
            raise SyntaxError("\n" + self.print_pos() + f"Expected {["<", ">", "==", "!=", ">=", "<="]} token got {tok} token.")

        self.eat()
        return Node(tok, "inequality-signs")
    
    def parse_condition_word(self) -> Node:
        tok = self.current()
        
        if tok is None:
            raise SyntaxError("\n" + self.print_pos() + f"Unexpected end of token sequence got {tok} token.")
        elif tok.pos not in ["NOUN", "NUMR", "ADVB", "ADJS", "ADJF", "PRCL"]:
            raise SyntaxError("\n" + self.print_pos() + f"Expected {["NOUN", "NUMR", "ADVB", "ADJS", "ADJF"]} token got {tok} token with pos {tok.pos}.")

        self.eat()
        return Node(tok, "condition-word")
    
    def parse_sort_operator(self) -> Node:
        tok = self.current()
        
        if tok is None or tok.tok != "сортировать":
            return Node(Token("epsilon"), "sort-operator", [])
        elif tok.tok == "сортировать":
            self.eat()
            sort_node = Node(tok, "sort")
            
            tok = self.expect("по")
            prep1_node = Node(tok, "prep")
            
            col_node = self.parse_column()
            
            tok = self.current()
            
            if tok is None:
                return Node(Token(""), "sort-operator", [sort_node, prep1_node, col_node])
            else:
                tok = self.expect("по")
                prep2_node = Node(tok, "prep")
            
                order_node = self.parse_order()
            
                return Node(Token(""), "sort-operator", [sort_node, prep1_node, col_node, prep2_node, order_node])

    def parse_order(self) -> Node:
        tok = self.current()
        
        if tok is None:
            return Node(Token("epsilon"), "order", [])
        elif tok.tok in ["возрастанию", "убыванию"]:
            self.eat()
            return Node(tok, rule="order")
        
        raise SyntaxError("\n" + self.print_pos() + f"Expected {["возрастанию", "убыванию", "epsilon"]}, got {tok}")
    
    def parse_limit_operator(self) -> Node:
        tok = self.current()
        
        if tok is None or tok.tok != "ограничить":
            return Node(Token("epsilon"), "limit-operator", [])
        
        self.eat()
        limit_node = Node(tok, "limit")
        
        num_tok = self.current()
        if num_tok is None or num_tok.pos != "NUMR":
            raise SyntaxError("\n" + self.print_pos() + f"Expected NUMR got {num_tok.tok} with pos {num_tok.pos}.")
        
        num_node = Node(num_tok, "numr")
        self.eat()
        
        return Node(Token(""), "limit-operator", [limit_node, num_node])
    