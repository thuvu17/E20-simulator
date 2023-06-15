Thu Vu
tnv2002@nyu.edu

Assignment completed. No known bugs.

The program read in the machine code, executed the instructions, then display the
result and the value of the first 128 memory cells. No other sources were used.

Design choice:

1) Lists are used to store memory set and values of 7 register values, all initialized
   to ZERO.

2) Program counter is initialized to ZERO.

3) The simulator will stop whenever it sees a halt instruction. So a boolean (halt) is
   used to identify the halt instruction and stop the while loop.

4) Whenever an instruction sets a register to a value outside of the range of a 16-bit
   number, the program will handle overflow.

5) Immediate values in arithmetic instructions are 7-bit signed numbers. Overflow of
   immediate values is also handled by the program.

6) The range of pc is from 0-8191. Overflow is handled. If pc goes over 8191, the
   program will not crash but loops back to 0.