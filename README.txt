Thu Vu
tnv2002@nyu.edu

Assignment completed. No know bugs.

The program read in the machine code, execute the instructions, simulate caching and display
cache configuration.


DESIGN CHOICES:

Cache table is indexed by row number and store tags. It is initialized as a list of lists.
The reason for doing this is due to associativity. In order to store multiple tags in one
row, I choose to use sublists.

In exeInstr_getAddr function, a function that executes the instructions like project 2,
pc is not incremented for sw and lw. That will be done after caching since we have to print
log entry with old pc value.

I keep track of LRU by the order of insertion to the list. The items at the end of the list
are the ones most recently used. To implement this, whenever an address is accessed, if
it's not already in the cache - push, if it's already cached - pop it and push back to the
end of the list. That way, the most recently access items will always be at the end.

How caching works in my program:

   IF 1 CACHE: If MISS and row is full, evict LRU. If HIT, remove the tag from the row. For
   both cases, push the tag to the end of the row.

   IF 2 CACHE: Use the same function as 1 cache. The logic should still apply. If L1 HIT,
   skip L2. If L1 MISS, using the same function, we would've already write to L1, we can
   safely move to L2. L2 would then use the same function (move up tag if HIT, write if MISS)


REFERENCES: 
E20 manual