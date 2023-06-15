ccccc[=[========[=#!/usr/bin/python3

"""
CS-UY 2214
Jeff Epstein
Starter code for E20 simulator
sim.py
"""

from collections import namedtuple
import re
import argparse

# Some helpful constant values that we'll be using.
Constants = namedtuple("Constants",["NUM_REGS", "MEM_SIZE", "REG_SIZE"])
constants = Constants(NUM_REGS = 8, 
                      MEM_SIZE = 2**13,
                      REG_SIZE = 2**16)

def load_machine_code(machine_code, mem):
    """
    Loads an E20 machine code file into the list
    provided by mem. We assume that mem is
    large enough to hold the values in the machine
    code file.
    sig: list(str) -> list(int) -> NoneType
    """
    machine_code_re = re.compile("^ram\[(\d+)\] = 16'b(\d+);.*$")
    expectedaddr = 0
    for line in machine_code:
        match = machine_code_re.match(line)
        if not match:
            raise ValueError("Can't parse line: %s" % line)
        addr, instr = match.groups()
        addr = int(addr,10)
        instr = int(instr,2)
        if addr != expectedaddr:
            raise ValueError("Memory addresses encountered out of sequence: %s" % addr)
        if addr >= len(mem):
            raise ValueError("Program too big for memory")
        expectedaddr += 1
        mem[addr] = instr

def print_state(pc, regs, memory, memquantity):
    """
    Prints the current state of the simulator, including
    the current program counter, the current register values,
    and the first memquantity elements of memory.
    sig: int -> list(int) -> list(int) - int -> NoneType
    """
    print("Final state:")
    print("\tpc="+format(pc,"5d"))
    for reg, regval in enumerate(regs):
        print(("\t$%s=" % reg)+format(regval,"5d"))
    line = ""
    for count in range(memquantity):
        line += format(memory[count], "04x")+ " "
        if count % 8 == 7:
            print(line)
            line = ""
    if line != "":
        print(line)

def main():
    parser = argparse.ArgumentParser(description='Simulate E20 machine')
    parser.add_argument('filename', help='The file containing machine code, typically with .bin suffix')
    cmdline = parser.parse_args()

    # initialize memory set, registers, program counter, and a bool to identify halt
    mem = [0] * constants.MEM_SIZE
    regs = [0] * constants.NUM_REGS
    pc = 0
    halt = False

    # load machine code into mem
    with open(cmdline.filename) as file:
        load_machine_code(file, mem)

    # execute instructions
    while halt is False:
        instr = mem[pc % constants.REG_SIZE]
        # if halt, break
        if instr == 16384 + pc:
            halt = True
            break
        opCode = (instr >> 13) & 7
        regB = (instr >> 7) & 7
        regA = (instr >> 10) & 7
        # j or jal
        if opCode == 2 or opCode == 3:
            if opCode == 3: # jal
                regs[7] = (pc + 1) % constants.REG_SIZE
            pc = instr & 8191
        # three reg instructions
        elif opCode == 0:
            last4Bit = instr & 15
            regDst = (instr >> 4) & 7
            if last4Bit == 8: # jr
                pc = regs[regA]
            elif last4Bit == 4: # slt
                regs[regDst] = 1 if (regs[regA] < regs[regB]) else 0
                pc += 1
            else:
                if last4Bit == 0: # add
                    regs[regDst] = regs[regA] + regs[regB]
                elif last4Bit == 1: # sub
                    regs[regDst] = regs[regA] - regs[regB]
                elif last4Bit == 2: # or
                    regs[regDst] = regs[regA] | regs[regB]
                elif last4Bit == 3: # and
                    regs[regDst] = regs[regA] & regs[regB]
                pc += 1
            regs[regDst] %= constants.REG_SIZE  # overflow
        # two reg instructions
        else:
            imm = (instr & 127) if ((instr & 127) <= 63) else -64 + ((instr & 127) - 64) # overflow
            # if not jeq, increment pc by 1
            if opCode != 6:
                pc += 1
            if opCode == 7: # slti
                imm = (instr & 127) | 65408     # get sign-extended imm
                regs[regB] = 1 if (regs[regA] & 65535 < imm) else 0
            elif opCode == 4: # lw
                regs[regB] = mem[(regs[regA] + imm) % 2**13]
            elif opCode == 5: # sw
                mem[(regs[regA] + imm) % constants.MEM_SIZE] = regs[regB]
            elif opCode == 6: # jeq
                pc += 1 + imm if (regs[regA] == regs[regB]) else 1
            elif opCode == 1: # addi
                regs[regB] = regs[regA] + imm
            regs[regB] %= constants.REG_SIZE    # overflow
        regs[0] = 0 # prevent modifying $0
        pc %= constants.MEM_SIZE    # overflow


    # display the result and the first 128 memory cells value
    print_state(pc, regs, mem, 128)

if __name__ == "__main__":
    main()
#ra0Eequ6ucie6Jei0koh6phishohm9
