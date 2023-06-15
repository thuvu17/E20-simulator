#!/usr/bin/python3

"""
CS-UY 2214
Jeff Epstein
Starter code for E20 cache simulator
simcache.py
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

def print_cache_config(cache_name, size, assoc, blocksize, num_rows):
    """
    Prints out the correctly-formatted configuration of a cache.

    cache_name -- The name of the cache. "L1" or "L2"

    size -- The total size of the cache, measured in memory cells.
        Excludes metadata

    assoc -- The associativity of the cache. One of [1,2,4,8,16]

    blocksize -- The blocksize of the cache. One of [1,2,4,8,16,32,64])

    num_rows -- The number of rows in the given cache.

    sig: str, int, int, int, int -> NoneType
    """

    summary = "Cache %s has size %s, associativity %s, " \
        "blocksize %s, rows %s" % (cache_name,
        size, assoc, blocksize, num_rows)
    print(summary)

def print_log_entry(cache_name, status, pc, addr, row):
    """
    Prints out a correctly-formatted log entry.

    cache_name -- The name of the cache where the event
        occurred. "L1" or "L2"

    status -- The kind of cache event. "SW", "HIT", or
        "MISS"

    pc -- The program counter of the memory
        access instruction

    addr -- The memory address being accessed.

    row -- The cache row or set number where the data
        is stored.

    sig: str, str, int, int, int -> NoneType
    """
    log_entry = "{event:8s} pc:{pc:5d}\taddr:{addr:5d}\t" \
        "row:{row:4d}".format(row=row, pc=pc, addr=addr,
            event = cache_name + " " + status)
    print(log_entry)


# take in cache, cache size, blocksize, and associativity - return number of row
# and print cache configuration
def getNumRow_printConfig(cacheName, cacheSize, blocksize, assoc):
    numRow = cacheSize // (blocksize * assoc)
    print_cache_config(cacheName, cacheSize, assoc, blocksize, numRow)
    return numRow


# project 2 code: take in instruction machine code, list of registers, pc, memory
# execute the instruction like normal - return mem addr if sw or lw for caching
def exeInstr_getAddr(instr, regs, var, mem):
    opCode = (instr >> 13) & 7
    regB = (instr >> 7) & 7
    regA = (instr >> 10) & 7
    # j or jal
    if opCode == 2 or opCode == 3:
        if opCode == 3: # jal
            regs[7] = (var[0] + 1) % constants.REG_SIZE
        var[0] = instr & 8191
    # three reg instructions
    elif opCode == 0:
        last4Bit = instr & 15
        regDst = (instr >> 4) & 7
        if last4Bit == 8: # jr
            var[0] = regs[regA]
        elif last4Bit == 4: # slt
            regs[regDst] = 1 if (regs[regA] < regs[regB]) else 0
            var[0] += 1
        else:
            if last4Bit == 0: # add
                regs[regDst] = regs[regA] + regs[regB]
            elif last4Bit == 1: # sub
                regs[regDst] = regs[regA] - regs[regB]
            elif last4Bit == 2: # or
                regs[regDst] = regs[regA] | regs[regB]
            elif last4Bit == 3: # and
                regs[regDst] = regs[regA] & regs[regB]
            var[0] += 1
        regs[regDst] %= constants.REG_SIZE  # overflow
    # two reg instructions
    else:
        imm = (instr & 127) if ((instr & 127) <= 63) else (instr & 127) - 128 # overflow
        # if not jeq, sw, or lw, increment pc by 1
        if opCode != 4 and opCode != 5 and opCode != 6:
            var[0] += 1
        if opCode == 7: # slti
            if (instr & 127) & 64 == 64:
                imm = (instr & 127) | 65408     # get sign-extended imm
            regs[regB] = 1 if (regs[regA] < imm) else 0
        elif opCode == 4: # lw
            regs[regB] = mem[(regs[regA] + imm) % constants.MEM_SIZE]
        elif opCode == 5: # sw
            mem[(regs[regA] + imm) % constants.MEM_SIZE] = regs[regB]
        elif opCode == 6: # jeq
            var[0] += 1 + imm if (regs[regA] == regs[regB]) else 1
        elif opCode == 1: # addi
            regs[regB] = regs[regA] + imm
        regs[regB] %= constants.REG_SIZE    # overflow

    regs[0] = 0 # prevent modifying $0
    var[0] %= constants.REG_SIZE    # overflow pc

    # if sw or lw (instr that uses cache), return mem address
    if opCode == 4 or opCode == 5:
        return (regs[regA] + imm) % constants.MEM_SIZE
    

# take in add, num of rows, blocksize - return row and tag    
def getRowTag(addr, numRows, blocksize):
    return (addr // blocksize) % numRows, (addr // blocksize) // numRows


# take in cmd(SW or LW), cache and name, row, tag, assoc, pc, addr
# execute caching, print log entry and return status(HIT or MISS)
def exeCache_getStatus(cmd, cacheName, cache, row, tag, assoc, pc, addr):
    # if miss, evict LRU if row is full
    if tag not in cache[row]:
        if len(cache[row]) == assoc:
            cache[row].pop(0)
        status = "MISS"
    # if hit, remove block and then add to the end (keep track of LRU)
    else:
        cache[row].remove(tag)
        status = "HIT"
    cache[row].append(tag)      # add block to cache
    if cmd == "SW":
        status = cmd
    print_log_entry(cacheName, status, pc, addr, row)
    return status


def main():
    parser = argparse.ArgumentParser(description='Simulate E20 cache')
    parser.add_argument('filename', help=
        'The file containing machine code, typically with .bin suffix')
    parser.add_argument('--cache', help=
        'Cache configuration: size,associativity,blocksize (for one cache) '
        'or size,associativity,blocksize,size,associativity,blocksize (for two caches)')
    cmdline = parser.parse_args()

    # variables
    mem = [0] * constants.MEM_SIZE      # memory
    regs = [0] * constants.NUM_REGS     # list of registers
    var = [0, False]
    # var [pc, halt]

    # load machine code into mem
    with open(cmdline.filename) as file:
        load_machine_code(file, mem)

    if cmdline.cache is not None:
        parts = cmdline.cache.split(",")
        # 1 CACHE SYSTEM
        if len(parts) == 3:
            # get cache size, num rows, assoc, blocksize and initialize cache table
            [L1size, L1assoc, L1blocksize] = [int(x) for x in parts]
            L1rows = getNumRow_printConfig("L1", L1size, L1blocksize, L1assoc)
            cache = [[] for _ in range(L1rows)]     # a list of empty lists
            # execute program
            while var[1] is False:
                instr = mem[var[0] % constants.MEM_SIZE]
                # if halt, break
                if instr == 16384 + var[0]:
                    var[1] = True
                    break
                addr = exeInstr_getAddr(instr, regs, var, mem)
                # if lw or sw, do caching:
                if addr is not None:
                    cmd = "LW" if (instr >> 13) & 7 == 4 else "SW"
                    row, tag = getRowTag(addr, L1rows, L1blocksize)
                    exeCache_getStatus(cmd, "L1", cache, row, tag, L1assoc, var[0], addr)
                    var[0] += 1
            
        # 2 CACHE SYSTEM
        elif len(parts) == 6:
            [L1size, L1assoc, L1blocksize, L2size, L2assoc, L2blocksize] = \
                [int(x) for x in parts]
            # TODO: execute E20 program and simulate two caches here
            # get number of rows
            L1rows = getNumRow_printConfig("L1", L1size, L1blocksize, L1assoc)
            L2rows = getNumRow_printConfig("L2", L2size, L2blocksize, L2assoc)
            # initialize cache
            cache1 = [[] for _ in range(L1rows)]
            cache2 = [[] for _ in range(L2rows)]
            # execute program
            while var[1] is False:
                instr = mem[var[0] % constants.MEM_SIZE]
                # if halt, break
                if instr == 16384 + var[0]:
                    var[1] = True
                    break
                addr = exeInstr_getAddr(instr, regs, var, mem)
                # if lw or sw, do caching
                if addr is not None:
                    cmd = "LW" if (instr >> 13) & 7 == 4 else "SW"
                    row1, tag1 = getRowTag(addr, L1rows, L1blocksize)
                    # cache L1 first. get L1 status to determine whether to cache L2
                    status1 = exeCache_getStatus(cmd, "L1", cache1, row1, tag1, L1assoc, var[0], addr)
                    # if sw or L1 miss, cache L2
                    if cmd == "SW" or status1 == "MISS":
                        row2, tag2 = getRowTag(addr, L2rows, L2blocksize)
                        exeCache_getStatus(cmd, "L2", cache2, row2, tag2, L2assoc, var[0], addr)
                    var[0] += 1
        else:
            raise Exception("Invalid cache config")

if __name__ == "__main__":
    main()
#ra0Eequ6ucie6Jei0koh6phishohm9