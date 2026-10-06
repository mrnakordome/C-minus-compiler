# Names:
# Arqavan Tajik
# Ali Amini

# Student Numbers:
# 402170895
# 401170529

# Reference:
# Kenneth C. Louden, Compiler Construction: Principles and Practice, 1st Ed.

import sys
import traceback
import table

sys.setrecursionlimit(50000)

KEYWORDS = ["break", "else", "for", "if", "int", "return", "void", "goto", "switch", "case", "default", "while"]
SYMBOLS = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '/']

class Scanner:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.length = len(text)
        self.lineno = 1
        self.tokens_by_line = {}
        self.errors = []
        self.symbol_table = list(KEYWORDS)
        self.symbol_set = set(KEYWORDS)

    def peek(self):
        return self.text[self.pos] if self.pos < self.length else None

    def peek_next(self):
        return self.text[self.pos + 1] if self.pos + 1 < self.length else None

    def advance(self):
        if self.pos >= self.length:
            return None
        ch = self.text[self.pos]
        self.pos += 1
        if ch == '\n':
            self.lineno += 1
        return ch

    def add_token(self, line, token_type, lexeme):
        if line not in self.tokens_by_line:
            self.tokens_by_line[line] = []
        self.tokens_by_line[line].append(f"({token_type}, {lexeme})")

    def add_error(self, line, lexeme, error_type):
        self.errors.append((line, lexeme, error_type))

    def add_to_symbol_table(self, lexeme):
        if lexeme not in self.symbol_set:
            self.symbol_set.add(lexeme)
            self.symbol_table.append(lexeme)

    def is_letter(self, ch):
        return ch is not None and (('a' <= ch <= 'z') or ('A' <= ch <= 'Z'))

    def is_digit(self, ch):
        return ch is not None and ('0' <= ch <= '9')

    def is_id_char(self, ch):
        return self.is_letter(ch) or self.is_digit(ch) or ch == '_'

    def is_whitespace(self, ch):
        return ch in [' ', '\n', '\r', '\t', '\v', '\f']

    def is_symbol(self, ch):
        return ch in SYMBOLS

    def skip_whitespace(self):
        while self.peek() and self.is_whitespace(self.peek()):
            self.advance()

    def scan_number(self):
        start_line, lexeme = self.lineno, ""
        while self.is_digit(self.peek()):
            lexeme += self.advance()
        if self.peek() and (self.is_letter(self.peek()) or self.peek() == '_'):
            while self.peek() and self.is_id_char(self.peek()):
                lexeme += self.advance()
            self.add_error(start_line, lexeme, "Invalid number")
            return None
        if len(lexeme) > 1 and lexeme[0] == '0':
            self.add_error(start_line, lexeme, "Invalid number")
            return None
        return ("NUM", lexeme, start_line)

    def scan_id_or_invalid(self):
        start_line, lexeme = self.lineno, ""
        while self.peek() and not self.is_whitespace(self.peek()) and not self.is_symbol(self.peek()):
            lexeme += self.advance()
        if lexeme and self.is_letter(lexeme[0]) and all(self.is_id_char(c) for c in lexeme):
            if lexeme in KEYWORDS:
                return ("KEYWORD", lexeme, start_line)
            self.add_to_symbol_table(lexeme)
            return ("ID", lexeme, start_line)
        self.add_error(start_line, lexeme, "Invalid input")
        return None

    def scan_comment(self):
        start_line = self.lineno
        if self.peek() == '/' and self.peek_next() == '*':
            preview = "/*"
            self.advance()
            self.advance()
            while True:
                ch = self.peek()
                if not ch:
                    self.add_error(start_line, preview + "...", "Unclosed comment")
                    break
                if ch == '*' and self.peek_next() == '/':
                    self.advance()
                    self.advance()
                    break
                curr = self.advance()
                if curr != '\n' and len(preview) < 9:
                    preview += curr
        return None

    def get_next_token(self):
        while self.pos < self.length:
            ch = self.peek()

            if self.is_whitespace(ch):
                self.skip_whitespace()
                continue

            if ch == '/':
                if self.peek_next() == '*':
                    self.scan_comment()
                    continue
                line = self.lineno
                self.advance()
                return ("SYMBOL", "/", line)

            if self.is_digit(ch):
                t = self.scan_number()
                if t:
                    self.add_token(t[2], t[0], t[1])
                    return t
                continue

            if self.is_letter(ch) or ch == '_':
                t = self.scan_id_or_invalid()
                if t:
                    self.add_token(t[2], t[0], t[1])
                    return t
                continue

            if ch == '*' and self.peek_next() == '/':
                line = self.lineno
                self.advance()
                self.advance()
                self.add_error(line, "*/", "Unmatched comment")
                continue

            if self.is_symbol(ch):
                if ch == '=' and self.peek_next() == '=':
                    line = self.lineno
                    self.advance()
                    self.advance()
                    self.add_token(line, "SYMBOL", "==")
                    return ("SYMBOL", "==", line)
                line = self.lineno
                sym = self.advance()
                self.add_token(line, "SYMBOL", sym)
                return ("SYMBOL", sym, line)

            line = self.lineno
            self.add_error(line, self.advance(), "Invalid input")

        return ("EOF", "$", self.lineno + 1)


class CodeGenerator:
    def __init__(self):
        self.PB = []
        self.ss = []
        self.lhs_stack = []
        self.jump_stack = []
        self.label_stack = []
        self.call_stack = []
        
        self.symbol_table = [{}] 
        self.functions = {}
        
        self.break_stack = []
        self.switch_stack = []
        self.labels = {}
        self.pending_gotos = {}
        
        self.data_ptr = 1000
        self.temp_ptr = 5000
        
        self.current_function = None
        self.arg_stack = [] 
        self.in_params = False
        
        self.last_decl_addr = None
        self.last_decl_offset = None
        self.last_decl_id = None
        self.last_decl_is_global = True
        
        self.semantic_errors = []
        self.current_type = "int"

        # Initialize the dynamic Stack Pointer (SP) at memory address 0 to value 10000
        self.emit("ASSIGN", "#10000", "0", "")
        # Pre-initialize temporary variables to mathematically guarantee no uninitialized bounds crashes
        self.emit("ASSIGN", "#4908", "4900", "")
        self.emit("LT", "4900", "{FINAL_TEMP}", "4904")
        self.emit("JPF", "4904", "7", "")
        self.emit("ASSIGN", "#0", "@4900", "")
        self.emit("ADD", "4900", "#4", "4900")
        self.emit("JP", "2", "", "")

    def get_temp(self):
        t = self.temp_ptr
        self.temp_ptr += 4
        return str(t)

    def lookup_symbol(self, name):
        if name in KEYWORDS or name in ["output", "input", "main"]:
            return {'address': name, 'type': 'keyword', 'is_global': True}
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]
        return None

    def emit(self, op, arg1="", arg2="", arg3=""):
        self.PB.append(f"({op}, {arg1}, {arg2}, {arg3})")

    def pop_ss(self):
        return self.ss.pop() if self.ss else {'val': '', 'type': 'int'}

    def call_action(self, action_name, token, lookahead=None):
        tok_class, lexeme, line = token

        if tok_class == "ID":
            self.last_id = lexeme
            
        if action_name == "type_int":
            self.current_type = "int"
        elif action_name == "type_void":
            self.current_type = "void"

        elif action_name == "declare_id":
            if lexeme and lexeme not in KEYWORDS and lexeme not in ["$", ";", ")", "}", "{", "(", ",", "output", "main"]:
                is_global = len(self.symbol_table) == 1
                
                if is_global:
                    addr = self.data_ptr
                    self.symbol_table[-1][lexeme] = {'address': addr, 'type': self.current_type, 'is_global': True}
                    self.data_ptr += 4
                    self.last_decl_addr = addr
                    self.last_decl_id = lexeme
                    self.last_decl_is_global = True
                    if not getattr(self, 'in_params', False):
                        self.emit("ASSIGN", "#0", str(addr), "")
                else:
                    offset = self.local_offset
                    self.symbol_table[-1][lexeme] = {'offset': offset, 'type': self.current_type, 'is_global': False}
                    self.local_offset += 4
                    self.last_decl_offset = offset
                    self.last_decl_id = lexeme
                    self.last_decl_is_global = False
                    
                    if getattr(self, 'in_params', False):
                        self.functions[self.current_function]['param_count'] += 1
                        self.functions[self.current_function]['param_types'].append(self.current_type)
                    else:
                        t1 = self.get_temp()
                        self.emit("ADD", "0", f"#{offset}", t1)
                        self.emit("ASSIGN", "#0", f"@{t1}", "")
                    
        elif action_name == "check_void_var":
            if self.current_type == "void":
                self.semantic_errors.append(f"#{line} : Semantic Error! Illegal type of void for '{self.last_id}'.")

        elif action_name == "make_array_param":
            self.symbol_table[-1][self.last_decl_id]['type'] = 'array'
            if self.current_function and self.current_function in self.functions:
                self.functions[self.current_function]['param_types'][-1] = 'array'

        elif action_name == "init_assign":
            if self.ss:
                val = self.pop_ss()
                decl_type = self.current_type
                if self.last_decl_id and self.last_decl_id in self.symbol_table[-1]:
                    decl_type = self.symbol_table[-1][self.last_decl_id]['type']
                if val['type'] != decl_type:
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {val['type']} instead of {decl_type}.")
                
                if getattr(self, 'last_decl_is_global', True):
                    self.emit("ASSIGN", val['val'], str(self.last_decl_addr), "")
                else:
                    t1 = self.get_temp()
                    self.emit("ADD", "0", f"#{self.last_decl_offset}", t1)
                    self.emit("ASSIGN", val['val'], f"@{t1}", "")
                
        elif action_name == "pop_stmt":
            if self.ss:
                self.pop_ss()

        elif action_name == "alloc_array":
            size_str = self.pop_ss()['val']
            size = int(size_str.replace("#", ""))
            
            if self.last_decl_id in self.symbol_table[-1]:
                self.symbol_table[-1][self.last_decl_id]['type'] = 'array'
                
            if getattr(self, 'last_decl_is_global', True):
                start_addr = self.data_ptr
                self.emit("ASSIGN", f"#{start_addr}", str(self.last_decl_addr), "")
                for i in range(size):
                    self.emit("ASSIGN", "#0", str(start_addr), "")
                    start_addr += 4
                self.data_ptr += size * 4
            else:
                elements_offset = self.local_offset
                self.local_offset += size * 4
                
                t_ptr = self.get_temp()
                self.emit("ADD", "0", f"#{elements_offset}", t_ptr)
                t_var = self.get_temp()
                self.emit("ADD", "0", f"#{self.last_decl_offset}", t_var)
                self.emit("ASSIGN", t_ptr, f"@{t_var}", "")
                
                for i in range(size):
                    t_elem = self.get_temp()
                    self.emit("ADD", "0", f"#{elements_offset + i*4}", t_elem)
                    self.emit("ASSIGN", "#0", f"@{t_elem}", "")

        elif action_name == "array_idx":
            idx = self.pop_ss()
            if idx['type'] != 'int':
                self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {idx['type']} instead of int.")
            base_addr = self.pop_ss()
            
            if base_addr['type'] != 'array':
                self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {base_addr['type']} instead of array.")
                
            t1 = self.get_temp()
            self.emit("MULT", idx['val'], "#4", t1)
            t2 = self.get_temp()
            self.emit("ADD", base_addr['val'], t1, t2)
            self.ss.append({'val': f"@{t2}", 'type': 'int'})

        elif action_name == "pid":
            if lexeme and lexeme not in KEYWORDS and lexeme not in ["$", ";", ")", "}", "{", "(", ","]:
                if lookahead and lookahead[1] == ':':
                    self.ss.append({'val': lexeme, 'type': 'label'})
                    return
                if lexeme == "output":
                    self.ss.append({'val': 'output', 'type': 'keyword'})
                    return
                if lexeme == "main":
                    self.ss.append({'val': 'main', 'type': 'keyword'})
                    return
                    
                sym = self.lookup_symbol(lexeme)
                if sym:
                    if sym.get('is_global', False):
                        self.ss.append({'val': str(sym['address']), 'type': sym['type']})
                    else:
                        t1 = self.get_temp()
                        self.emit("ADD", "0", f"#{sym['offset']}", t1)
                        self.ss.append({'val': f"@{t1}", 'type': sym['type']})
                else:
                    self.semantic_errors.append(f"#{line} : Semantic Error! '{lexeme}' is not defined.")
                    self.ss.append({'val': str(self.data_ptr), 'type': 'int'})

        elif action_name == "pnum":
            if lexeme and lexeme not in ["$", ";", ")", "}", "{", "(", ","]:
                self.ss.append({'val': f"#{lexeme}", 'type': 'int'})

        elif action_name == "prep_assign":
            if self.ss:
                self.lhs_stack.append(self.pop_ss())

        elif action_name == "assign":
            if self.ss and self.lhs_stack:
                rhs = self.pop_ss()
                lhs = self.lhs_stack.pop()
                if lhs['type'] != rhs['type']:
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {lhs['type']} instead of {rhs['type']}.")
                self.emit("ASSIGN", rhs['val'], lhs['val'], "")
                self.ss.append(lhs)

        # FIXED: Operators push safely onto the Semantic Stack, protecting math operations 
        # from being overwritten by nested recursive calls like fact(n-1) + fact(n-2)
        elif action_name == "set_add": self.ss.append({'val': 'ADD', 'type': 'op'})
        elif action_name == "set_sub": self.ss.append({'val': 'SUB', 'type': 'op'})
        elif action_name == "set_lt": self.ss.append({'val': 'LT', 'type': 'op'})
        elif action_name == "set_eq": self.ss.append({'val': 'EQ', 'type': 'op'})
        elif action_name == "set_mult": self.ss.append({'val': 'MULT', 'type': 'op'})
        elif action_name == "set_div": self.ss.append({'val': 'DIV', 'type': 'op'})

        elif action_name == "addop":
            if len(self.ss) >= 3:
                rhs = self.pop_ss()
                op = self.pop_ss()['val']
                lhs = self.pop_ss()
                if lhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {lhs['type']} instead of int.")
                if rhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {rhs['type']} instead of int.")
                temp = self.get_temp()
                self.emit(op, lhs['val'], rhs['val'], temp)
                self.ss.append({'val': temp, 'type': 'int'})

        elif action_name == "mult":
            if len(self.ss) >= 3:
                rhs = self.pop_ss()
                op = self.pop_ss()['val']
                lhs = self.pop_ss()
                if lhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {lhs['type']} instead of int.")
                if rhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {rhs['type']} instead of int.")
                temp = self.get_temp()
                self.emit(op, lhs['val'], rhs['val'], temp)
                self.ss.append({'val': temp, 'type': 'int'})

        elif action_name == "relop":
            if len(self.ss) >= 3:
                rhs = self.pop_ss()
                op = self.pop_ss()['val']
                lhs = self.pop_ss()
                if lhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {lhs['type']} instead of int.")
                if rhs['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {rhs['type']} instead of int.")
                temp = self.get_temp()
                self.emit(op, lhs['val'], rhs['val'], temp)
                self.ss.append({'val': temp, 'type': 'int'})

        elif action_name == "pos":
            if self.ss:
                val = self.pop_ss()
                if val['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {val['type']} instead of int.")
                self.ss.append({'val': val['val'], 'type': 'int'})
                
        elif action_name == "neg":
            if self.ss:
                val = self.pop_ss()
                if val['type'] != 'int':
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {val['type']} instead of int.")
                temp = self.get_temp()
                self.emit("SUB", "#0", val['val'], temp)
                self.ss.append({'val': temp, 'type': 'int'})

        elif action_name == "save":
            condition = self.pop_ss()
            self.jump_stack.append({'type': 'jpf', 'index': len(self.PB), 'cond': condition['val']})
            self.emit("JPF", condition['val'], "", "")

        elif action_name == "jpf_save":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'jpf':
                jpf_info = self.jump_stack.pop()
                self.PB[jpf_info['index']] = f"(JPF, {jpf_info['cond']}, {len(self.PB) + 1}, )"
            self.jump_stack.append({'type': 'jp', 'index': len(self.PB)})
            self.emit("JP", "", "", "")

        elif action_name == "jp_end":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'jp':
                jp_info = self.jump_stack.pop()
                self.PB[jp_info['index']] = f"(JP, {len(self.PB)}, , )"
                
        elif action_name == "jp_end_eps":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'jpf':
                jpf_info = self.jump_stack.pop()
                self.PB[jpf_info['index']] = f"(JPF, {jpf_info['cond']}, {len(self.PB)}, )"

        elif action_name == "start_loop":
            self.break_stack.append([])

        elif action_name == "label":
            self.label_stack.append(len(self.PB))

        elif action_name == "while_end":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'jpf':
                jpf_info = self.jump_stack.pop()
                if self.label_stack:
                    self.emit("JP", self.label_stack.pop(), "", "")
                self.PB[jpf_info['index']] = f"(JPF, {jpf_info['cond']}, {len(self.PB)}, )"
                
            if self.break_stack:
                for b_idx in self.break_stack.pop():
                    self.PB[b_idx] = f"(JP, {len(self.PB)}, , )"

        elif action_name == "break_jump":
            if self.break_stack:
                self.break_stack[-1].append(len(self.PB))
                self.emit("JP", "", "", "")
            else:
                self.semantic_errors.append(f"#{line} : Semantic Error! No 'while' found for 'break'.")

        elif action_name == "def_label":
            label_name = self.last_id
            self.pop_ss() 
            curr_line = len(self.PB)
            self.labels[label_name] = curr_line
            for pb_idx in self.pending_gotos.get(label_name, []):
                self.PB[pb_idx] = f"(JP, {curr_line}, , )"
            self.pending_gotos.pop(label_name, None)

        elif action_name == "goto_jump":
            label_name = self.last_id
            if label_name in self.labels:
                self.emit("JP", self.labels[label_name], "", "")
            else:
                self.pending_gotos.setdefault(label_name, []).append(len(self.PB))
                self.emit("JP", "UNKNOWN", "", "") 

        elif action_name == "save_switch":
            switch_val = self.pop_ss()
            matched_flag = self.get_temp()
            self.emit("ASSIGN", "#0", matched_flag, "")
            self.switch_stack.append({'val': switch_val['val'], 'match': matched_flag})

        elif action_name == "case_check":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'case_jpf':
                prev_jpf = self.jump_stack.pop()
                self.PB[prev_jpf['index']] = f"(JPF, {prev_jpf['cond']}, {len(self.PB)}, )"
            
            case_val = self.pop_ss()
            switch_info = self.switch_stack[-1]
            sw_val = switch_info['val']
            match_flag = switch_info['match']
            
            t_eq = self.get_temp()
            temp = self.get_temp()
            self.emit("EQ", sw_val, case_val['val'], t_eq)
            self.emit("ADD", match_flag, t_eq, temp)
            self.emit("ASSIGN", temp, match_flag, "")
            
            self.jump_stack.append({'type': 'case_jpf', 'index': len(self.PB), 'cond': temp})
            self.emit("JPF", temp, "", "")

        elif action_name == "default_check":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'case_jpf':
                prev_jpf = self.jump_stack.pop()
                self.PB[prev_jpf['index']] = f"(JPF, {prev_jpf['cond']}, {len(self.PB)}, )"

        elif action_name == "end_switch":
            if self.jump_stack and self.jump_stack[-1]['type'] == 'case_jpf':
                prev_jpf = self.jump_stack.pop()
                self.PB[prev_jpf['index']] = f"(JPF, {prev_jpf['cond']}, {len(self.PB)}, )"
            self.switch_stack.pop()
            if self.break_stack:
                for b_idx in self.break_stack.pop():
                    self.PB[b_idx] = f"(JP, {len(self.PB)}, , )"

        elif action_name == "func_start":
            self.in_params = True
            func_name = self.last_id if self.last_id else lexeme
            
            skip_line = None
            if func_name != "main":
                skip_line = len(self.PB)
                self.emit("JP", "UNKNOWN", "", "")

            self.functions[func_name] = {
                'start_line': len(self.PB),
                'skip_jp_line': skip_line,
                'param_count': 0,
                'param_types': [],
                'return_type': self.current_type,
                'first_temp': self.temp_ptr
            }
            
            self.symbol_table.append({})
            self.current_function = func_name
            self.local_offset = 8
            
        elif action_name == "end_params":
            self.in_params = False

        elif action_name == "func_end":
            if self.current_function and self.current_function != "main":
                ret_addr_temp = self.get_temp()
                self.emit("ADD", "0", "#4", ret_addr_temp)
                
                actual_ret_addr = self.get_temp()
                self.emit("ASSIGN", f"@{ret_addr_temp}", actual_ret_addr, "")
                self.emit("JP", f"@{actual_ret_addr}", "", "")
                
                skip_line = self.functions[self.current_function]['skip_jp_line']
                self.PB[skip_line] = f"(JP, {len(self.PB)}, , )"
                
            if len(self.symbol_table) > 1:
                self.symbol_table.pop()

        elif action_name == "mark_call":
            self.call_stack.append({'name': self.last_id, 'line': line})
            self.arg_stack.append([])

        elif action_name == "param":
            if self.ss:
                if not self.arg_stack:
                    self.arg_stack.append([])
                self.arg_stack[-1].append(self.pop_ss())

        elif action_name == "call":
            self.pop_ss() 
            func_info = self.call_stack.pop() if self.call_stack else None
            current_args = self.arg_stack.pop() if self.arg_stack else []
            
            if not func_info:
                return
                
            func_name = func_info['name']
            call_line = func_info['line']
            
            if func_name == "output":
                if len(current_args) != 1:
                    self.semantic_errors.append(f"#{call_line} : Semantic Error! Mismatch in numbers of arguments of 'output'.")
                
                arg_val = current_args.pop() if current_args else {'val': '#0', 'type': 'int'}
                self.emit("PRINT", arg_val['val'], "", "")
                self.ss.append({'val': "#0", 'type': 'void'}) 
                
            elif func_name in self.functions:
                func_data = self.functions[func_name]
                expected_count = func_data['param_count']
                
                if len(current_args) != expected_count:
                    self.semantic_errors.append(f"#{call_line} : Semantic Error! Mismatch in numbers of arguments of '{func_name}'.")
                else:
                    for i, arg_val in enumerate(current_args):
                        expected_type = func_data['param_types'][i]
                        if arg_val['type'] != expected_type:
                            self.semantic_errors.append(f"#{call_line} : Semantic Error! Mismatch in type of argument {i+1} of '{func_name}'. Expected '{expected_type}' but got '{arg_val['type']}' instead.")

                caller_ar_size = self.local_offset if self.current_function else 0
                first_temp = self.functions[self.current_function]['first_temp'] if self.current_function else 5000
                temp_count = (self.temp_ptr - first_temp) // 4
                
                for i in range(temp_count):
                    temp_addr = first_temp + i * 4
                    self.emit("ADD", "0", f"#{caller_ar_size + i*4}", "4996")
                    self.emit("ASSIGN", str(temp_addr), "@4996", "")
                    
                total_ar_size = caller_ar_size + temp_count * 4
                
                new_sp = self.get_temp()
                self.emit("ADD", "0", f"#{total_ar_size}", new_sp)
                
                for i, arg_val in enumerate(current_args):
                    param_loc = self.get_temp()
                    self.emit("ADD", new_sp, f"#{8 + i*4}", param_loc)
                    self.emit("ASSIGN", arg_val['val'], f"@{param_loc}", "")

                self.emit("ASSIGN", "#0", f"@{new_sp}", "") 
                
                ret_addr_loc = self.get_temp()
                self.emit("ADD", new_sp, "#4", ret_addr_loc)
                self.emit("ASSIGN", f"#{len(self.PB) + 3}", f"@{ret_addr_loc}", "")
                
                self.emit("ASSIGN", new_sp, "0", "")
                self.emit("JP", str(func_data['start_line']), "", "")
                
                self.emit("SUB", "0", f"#{total_ar_size}", "0")
                
                for i in range(temp_count):
                    temp_addr = first_temp + i * 4
                    self.emit("ADD", "0", f"#{caller_ar_size + i*4}", "4996")
                    self.emit("ASSIGN", "@4996", str(temp_addr), "")
                
                ret_val_loc = self.get_temp()
                self.emit("ADD", "0", f"#{total_ar_size}", ret_val_loc)
                
                res_temp = self.get_temp()
                self.emit("ASSIGN", f"@{ret_val_loc}", res_temp, "")
                        
                self.ss.append({'val': res_temp, 'type': func_data['return_type']})
            else:
                self.ss.append({'val': self.get_temp(), 'type': 'int'})

        elif action_name == "return_val":
            ret_val = self.pop_ss()
            if self.current_function and self.current_function != "main":
                expected = self.functions[self.current_function]['return_type']
                if ret_val['type'] != expected:
                    self.semantic_errors.append(f"#{line} : Semantic Error! Type mismatch in operands, Got {expected} instead of {ret_val['type']}.")
                
                ret_loc = self.get_temp()
                self.emit("ADD", "0", "#0", ret_loc)
                self.emit("ASSIGN", ret_val['val'], f"@{ret_loc}", "")
                
                ret_addr = self.get_temp()
                self.emit("ADD", "0", "#4", ret_addr)
                
                actual_ret_addr = self.get_temp()
                self.emit("ASSIGN", f"@{ret_addr}", actual_ret_addr, "")
                self.emit("JP", f"@{actual_ret_addr}", "", "")
                
        elif action_name == "return_void":
            if self.current_function and self.current_function != "main":
                ret_addr = self.get_temp()
                self.emit("ADD", "0", "#4", ret_addr)
                
                actual_ret_addr = self.get_temp()
                self.emit("ASSIGN", f"@{ret_addr}", actual_ret_addr, "")
                self.emit("JP", f"@{actual_ret_addr}", "", "")

    def write_output(self):
        with open("semantic_errors.txt", "w", encoding="utf-8") as f:
            if not self.semantic_errors:
                f.write("The input program is semantically correct.\n")
            else:
                for err in self.semantic_errors:
                    f.write(f"{err}\n")

        with open("output.txt", "w", encoding="utf-8") as f:
            if self.semantic_errors or not self.PB or len(self.PB) == 0:
                f.write("The output code has not been generated\n")
            else:
                for idx, code in enumerate(self.PB):
                    code = code.replace("{FINAL_TEMP}", f"#{self.temp_ptr}")
                    f.write(f"{idx}\t{code}\n")


class Parser:
    def __init__(self, scanner):
        self.scanner = scanner
        self.lookahead = self.scanner.get_next_token()
        self.last_token = self.lookahead
        self.syntax_errors = []
        self.predict_table = table.PREDICT
        self.follow_sets = table.FOLLOW
        self.rules = table.RULES
        self.code_gen = CodeGenerator()

    def get_token_type(self, token):
        tok_type, lexeme, _ = token
        if tok_type == "EOF": return "$"
        if tok_type == "ID": return "ID"
        if tok_type == "NUM": return "NUM"
        return lexeme

    def parse(self):
        stack = ["$", "Program"]
        loop_counter = 0
        max_loops = 100000

        while stack:
            loop_counter += 1
            if loop_counter > max_loops:
                self.add_error(self.lookahead[2], f"unexpected token {self.lookahead[1]}")
                break

            top_symbol = stack.pop()
            token_type = self.get_token_type(self.lookahead)

            if top_symbol.startswith("#"):
                action_name = top_symbol[1:]
                self.code_gen.call_action(action_name, self.last_token, self.lookahead)
                continue

            if top_symbol == "$":
                break

            if top_symbol in self.predict_table:
                rule_id = self.predict_table[top_symbol].get(token_type)
                if rule_id is not None:
                    rhs = self.rules[rule_id]
                    if rhs != ["EPSILON"]:
                        for sym in reversed(rhs):
                            stack.append(sym)
                else:
                    if token_type in self.follow_sets.get(top_symbol, []) or token_type == "$":
                        self.add_error(self.lookahead[2], f"missing {top_symbol}")
                    else:
                        self.add_error(self.lookahead[2], f"illegal {token_type}")
                        self.last_token = self.lookahead
                        self.lookahead = self.scanner.get_next_token()
                        stack.append(top_symbol)
            else:
                if top_symbol == token_type:
                    self.last_token = self.lookahead
                    self.lookahead = self.scanner.get_next_token()
                else:
                    self.add_error(self.lookahead[2], f"missing {top_symbol}")

    def add_error(self, line, msg):
        self.syntax_errors.append(f"#{line} : syntax error, {msg}")

    def write_files(self):
        with open("parse_tree.txt", "w", encoding="utf-8") as f:
            f.write("Program\n")

        with open("syntax_errors.txt", "w", encoding="utf-8") as f:
            if not self.syntax_errors:
                f.write("The input program is semantically correct.\n")
            else:
                for err in self.syntax_errors:
                    f.write(f"{err}\n")
                    
        with open("tokens.txt", "w", encoding="utf-8") as f:
            for l in sorted(self.scanner.tokens_by_line.keys()):
                f.write(f"{l}.\t" + " ".join(self.scanner.tokens_by_line[l]) + "\n")

        with open("lexical_errors.txt", "w", encoding="utf-8") as f:
            if not self.scanner.errors:
                f.write("There is no lexical error.")
            else:
                for line, lex, err in self.scanner.errors:
                    f.write(f"{line}.\t({lex}, {err})\n")

        with open("symbol_table.txt", "w", encoding="utf-8") as f:
            for i, lex in enumerate(self.scanner.symbol_table, start=1):
                f.write(f"{i}.\t{lex}\n")

        self.code_gen.write_output()

if __name__ == "__main__":
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            text = f.read()

        scanner = Scanner(text)
        parser = Parser(scanner)
        parser.parse()

    except Exception as e:
        traceback.print_exc()

    finally:
        if 'parser' in locals():
            parser.write_files()