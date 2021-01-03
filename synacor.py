import inspect
import sys

MOD = 1 << 15
HLT, JMP, CNT = range(3)

opcodes = {}
def opcode(op):
    def deco(f):
        opcodes[op] = f
        return f
    return deco

cmds = {}
cmd_args = {}
def cmd(c):
    def deco(f):
        cmds[c] = f
        cmd_args[c] = inspect.getargs(f.__code__).args[1:]
        return f
    return deco

aps = {
    "l": ["look"],
    "i": ["inv"],
    "n": ["north"],
    "e": ["east"],
    "s": ["south"],
    "w": ["west"],
    "u": ["up"],
    "d": ["down"],
    "t": ["use teleporter"],
    "1": [
        "take tablet", "use tablet",
        "doorway", "n", "n", 
        "bridge", "continue", "d",
        "e", "take empty lantern",
        "w", "w", "passage", "ladder"
    ],
    "2": [
        *"1wsn",
        "take can", "use can",
        "use lantern",
        "w"
    ],
    "3": [
        "2", "ladder", "darkness", "continue",
        *"wwwwn",
        "take red coin", "n",
        "e", "take concave coin",
        "d", "take corroded coin", *"uw",
        "w", "take blue coin",
        "u", "take shiny coin", *"de",
    ] + [
        f"use {c} coin" for c in 
        "blue red shiny concave corroded".split()
    ] + ["n", "take teleporter", "t"],
    "4": [
        "3",
        "take business card",
        "look strange book",
        *"%t"
    ],
    "5": [
        *"4nnnnnnnnn",
        "take orb",
        *"neenwseewnne",
        "vault", "take mirror", "use mirror"
    ]
}

def get_from_ap(cmd):
    if cmd not in aps:
        return [cmd]
    return [y for x in aps[cmd] for y in get_from_ap(x)]

class VM:
    def __init__(self):
        self.memory = [0] * (1<<15)
        self.registers = [0] * 8
        self.stack = []
        self.pc = 0
        self.input_buffer = ""
        self.debug = False
        self.skip = 0
        self.watch = set()
        self.dis = {}
        self.jump_destinations = set()
    
    def load_program(self, path):
        with open(path, "rb") as file:
            program = list(file.read())
            for i in range(0, len(program), 2):
                low, high = program[i:i+2]
                self.memory[i>>1] = high<<8 | low
                
    def send_input(self, line):
        self.input_buffer += line + "\n"
    
    def read(self, value):
        if value < 1<<15:
            return value
        
        value -= 1<<15
        if value >= 8:
            raise ValueError
        
        if self.debug:
            print("<", f"r{value+1} =", self.registers[value], file=sys.stderr)
        
        return self.registers[value]
    
    def write(self, addr, value):
        if addr < 1<<15:
            raise ValueError
        
        addr -= 1<<15
        if addr >= 8:
            raise ValueError
        
        self.registers[addr] = value % MOD
        if self.debug:
            print(">", f"r{addr+1} =", self.registers[addr], file=sys.stderr)

    @opcode(0)
    def halt(self):
        return HLT
    
    @opcode(1)
    def set_(self, a, b):
        self.write(a, self.read(b))
        return CNT
    
    @opcode(2)
    def push(self, a):
        self.stack.append(self.read(a))
        return CNT
    
    @opcode(3)
    def pop(self, a):
        self.write(a, self.stack.pop())
        return CNT
    
    @opcode(4)
    def eq(self, a, b, c):
        self.write(a, self.read(b) == self.read(c))
        return CNT
    
    @opcode(5)
    def gt(self, a, b, c):
        self.write(a, self.read(b) > self.read(c))
        return CNT
    
    @opcode(6)
    def jmp(self, a):
        self.pc = self.read(a)
        return JMP
    
    @opcode(7)
    def jt(self, a, b):
        if self.read(a):
            self.pc = self.read(b)
            return JMP
        return CNT
    
    @opcode(8)
    def jf(self, a, b):
        if not self.read(a):
            self.pc = self.read(b)
            return JMP
        return CNT
    
    @opcode(9)
    def add(self, a, b, c):
        self.write(a, self.read(b) + self.read(c))
        return CNT
    
    @opcode(10)
    def mult(self, a, b, c):
        self.write(a, self.read(b) * self.read(c))
        return CNT
    
    @opcode(11)
    def mod(self, a, b, c):
        self.write(a, self.read(b) % self.read(c))
        return CNT
    
    @opcode(12)
    def and_(self, a, b, c):
        self.write(a, self.read(b) & self.read(c))
        return CNT
    
    @opcode(13)
    def or_(self, a, b, c):
        self.write(a, self.read(b) | self.read(c))
        return CNT
    
    @opcode(14)
    def not_(self, a, b):
        self.write(a, ~self.read(b))
        return CNT
    
    @opcode(15)
    def rmem(self, a, b):
        self.write(a, self.memory[self.read(b)])
        return CNT
    
    @opcode(16)
    def wmem(self, a, b):
        self.memory[self.read(a)] = self.read(b)
        return CNT
    
    @opcode(17)
    def call(self, a):
        self.stack.append(self.pc + 2)
        return self.jmp(a)
    
    @opcode(18)
    def ret(self):
        return self.jmp(self.stack.pop())
    
    @opcode(19)
    def out(self, a):
        print(end=chr(self.read(a)))
        return CNT
    
    @opcode(20)
    def in_(self, a):        
        if not self.input_buffer:
            for line in get_from_ap(self.get_input()):
                self.send_input(line)

        char, self.input_buffer = self.input_buffer[0], self.input_buffer[1:]
        if char == "%":
            self.registers[7] = 25734
            return self.in_(a)
        
        self.write(a, ord(char))
        return CNT
    
    @opcode(21)
    def noop(self):
        return CNT
    
    @cmd("help")
    def help_(self):
        print()
        print("=== Debug Commands ===")
        for cmd, args in cmd_args.items():
            print(cmd, *(f"<{a}>" for a in args))
        print()
    
    @cmd("r")
    def r(self):
        for i in range(8):
            print(f"r{i+1} = {self.registers[i]}")
    
    @cmd("rs")
    def rs(self, register, value):
        self.registers[int(register)-1] = int(value)
        
    @cmd("d")
    def d(self):
        self.debug = not self.debug
    
    @cmd("n")
    def n(self, steps):
        self.skip = int(steps)
    
    @cmd("w")
    def watch(self, registers):
        self.watch = {int(x)-1 for x in registers.split(",")}
    
    @cmd("dis")
    def write_dis(self):
        o = 0
        with open("dis.txt", "w") as file:
            for pc in sorted(self.dis):
                if pc in self.jump_destinations:
                    file.write("\n")
                file.write(self.dis[pc] + "\n")
                o += 1
        print(o, "lines have been written.")
        
    def get_input(self):
        while (inp := input("> ")).startswith("."):
            cmd, *args = inp[1:].split()
            if cmd not in cmds:
                print("Command not found:", cmd)
                continue
            if len(args) != len(cmd_args[cmd]):
                print("Usage:", cmd, *(f"<{a}>" for a in cmd_args[cmd]))
                continue
            cmds[cmd](self, *args)
        return inp
    
    def run(self):
        while self.pc < len(self.memory):
            op = self.memory[self.pc]
            if op not in opcodes:
                print(*self.memory[self.pc:self.pc+5])
                raise NotImplementedError(f"Unknown opcode: {op}")
            
            func = opcodes[op]
            argcnt = func.__code__.co_argcount - 1
            if self.pc + argcnt >= len(self.memory):
                raise ValueError
            
            args = self.memory[self.pc+1:self.pc+1+argcnt]
            if any(a-(1<<15) in self.watch for a in args):
                self.watch.clear()
            line = f"{self.pc}| {func.__name__.strip('_')}"
            for a in args:
                if a >= (1<<15):
                    a -= 1<<15
                    line += f" r{a+1}"
                else:
                    line += f" {a}"
            prev = self.dis.get(self.pc)
            self.dis[self.pc] = line
            if self.debug:
                print(line, file=sys.stderr)
                if prev and prev != line:
                    raise ValueError(f"Instruction changed at {self.pc=}")
                if self.skip:
                    self.skip -= 1
                elif not self.watch:
                    self.get_input()
                
            result = func(self, *args)
            if result == HLT:
                break
            elif result == CNT:
                self.pc += argcnt + 1
            elif result != JMP:
                raise ValueError
            else:
                self.jump_destinations.add(self.pc)
    
    def modify(self):
        self.memory[5485] = 6
        self.memory[5487] = (1<<15) + 7
        self.memory[5488] = 25734
        self.memory[5489] = 21
        self.memory[5490] = 21
    
    def disassemble(self):
        i = 0
        while i < len(self.memory):
            op = self.memory[i]
            if op !=16:#not in opcodes:
                i += 1
                continue
            func = opcodes[op]
            argcnt = func.__code__.co_argcount - 1
            args = self.memory[i+1:i+1+argcnt]
            print(i, func.__name__.strip("_"), *args)
            i += argcnt + 1

def main():
    from sys import argv
    
    vm = VM()
    vm.load_program("challenge.bin")
    vm.modify()
    if len(argv)>1:
        for x in get_from_ap(argv[1]):
            vm.send_input(x)
    vm.run()
                
if __name__ == "__main__":
    main()