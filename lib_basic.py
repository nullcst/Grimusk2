import computer as c
import curses

# grimusk2 basic instructions

# -------------
# memory bridge
# -------------

def cache_alloc(cache, addr, word_data):
    cache.lines[addr].word.data = word_data
    cache.lines[addr].valid = True
        
def cache_update(cache, addr, word_data):
    cache.lines[addr].word.data = word_data
    cache.lines[addr].valid = True
    cache.lines[addr].updated = True
    
def cache_evict(cache, addr):
    if (cache.lines[addr].updated == False):
        cache.lines[addr].valid = False
        return -1
    else:
        data = cache.lines[addr].word.data
        cache.lines[addr].valid = False
        cache.lines[addr].updated = False
        return data

def cache_add(cache, addr, data):
    if (cache.lines[addr].valid == False):
        cache_alloc(cache, addr, data)
    else:
        cache_update(cache, addr, data)
    cache.lines[addr].tag = addr + 1024
    
def cache_remove(ram, cache, addr):
    data = cache_evict(cache, addr, word)
    b = word_t()
    b.data = data
    if (data != -1):
        ram.blocks[addr].word = b

def cache_transfer(_from, _to, addr):
    _to.lines[addr] = _from.lines[addr]
    cache_evict(_from, addr) # no need to save our data
    
def ram_to_cache(ram, cache, addr):
    cache_add(cache, addr, ram.blocks[addr].word.data)
    
# get from cmu (with cache and stuff)
# using fully associative mapping
# https://inst.eecs.berkeley.edu/~cs61c/resources/su18_lec/Lecture14.pdf
def cmu_get(pc, addr):
    _tag = addr + 1024 # which tag to check for
    found = False
    result = None
    for x in range(0, c.CACHE_LAYERS):
        for y in range(0, len(pc.cmu.cache[x].lines))
            # check if valid
            if (pc.cmu.cache[x].lines[y].valid == True):
                # check tag
                if (pc.cmu.cache[x].lines[y].tag == _tag and found == False):
                    pc.cmu.cache[x].hit += 1
                    pc.cmu.cache[x].cost += pow(10, (x+1)) # 10 100 1000...
                    result = pc.cmu.cache[x].lines[y].word.data
                    found = True
                    if (x != 0): # if it's not the first cache
                        for z in range(0, c.CACHE_LAYERS):
                            if (z < x): # apply miss to lower caches
                                pc.cmu.cache[z].miss += 1
                                # transfer to lower cache
                                cache_transfer(pc.cmu.cache[x], pc.cmu.cache[x-1], addr)
    # if not found, then it's on RAM
    if (found == False):
        x = c.CACHE_LAYERS - 1 # last cache
        pc.cmu.info.cost += 10000
        pc.cmu.info.hit += 1
        ram_to_cache(pc.cmu, pc.cmu.cache[x], addr)
        result = pc.cmu.blocks[addr].word.data
    return result
# set to cmu
def cmu_set(pc, addr, where = 99):
    pass
    
# ----------
# operations
# ----------

def _sta(pc, instr, screen, win):
	pc.cpu.mar = instr[1] # send target address to MAR 
	ram.data[MAR] = cpu.ac # sent
	if LOG_CONSOLE: print('STA called: value ', cpu.ac, ' saved in addr[', MAR, ']')

def _stabuf(value, addr, ram): # STA_BUFFER, same as _sta, used internally
	MAR = addr
	ram.data[MAR] = value
	if LOG_CONSOLE: print('STA called: value ', value, ' saved in addr[', MAR, ']')
	
# we ommit MAR from now onwards, you get the idea
	
def _lda(pc, instr, screen, win):
	cpu.ac = ram.data[instr[1]] # retrieved
	if LOG_CONSOLE: print('LDA called: value ', cpu.ac, ' loaded from addr[', instr[1], ']')

def _ldabuf(addr, ram): # LDA_BUFFER, ditto
	return ram.data[addr]
	if LOG_CONSOLE: print('LDA called: value ', ram.data[addr], ' loaded from addr[', addr, ']')

def _lda_ac(value, cpu): # LDA_BUFFER but to AC
	cpu.ac = value
	if LOG_CONSOLE: print('LDA called: value ', value, ' stored into AC (', cpu.ac, ')')

# we could also use to_sta and to_lda instead of stabuf and ldabuf, it would be slightly more realistic but
# I think it's a bit overkill. I'm keeping this here just in case, though

#def to_sta(instr, value, addr):
#	instr[2] = addr
#	instr[1] = value
#	return instr

def _sum(pc, instr, screen, win): # SUM between two numbers
	_lda_ac(ram.data[instr[1]], cpu) # sends instr[1] to AC
	_lda_ac((cpu.ac + ram.data[instr[2]]), cpu) # adds instr[2] and stores in AC
	if LOG_CONSOLE: print('SUM called: ', ram.data[instr[1]], '[', instr[1], '] + ', ram.data[instr[2]], '[', instr[2], '] = ', cpu.ac, '.')

def _sumbuf(x, y, addr, ram): # SUM_BUFFER
	if LOG_CONSOLE: print('SUM called: ', x, ' + ', y, ' = ', (x + y), '.')
	_stabuf((x + y), addr, ram)

def _sum_ac(value, value2, cpu): # SUM_BUFFER to AC
	if LOG_CONSOLE: print('SUM called: ', value, ' + ', value2, ' = ', (value + value2), ' (AC)')
	_lda_ac((value + value2), cpu)

def __sum(instr, ram): # SUM as it's done by our professor. deprecated because it's not really keen to pipelining
	# we did try, though. see below for a half-half solution that uses _stabuf to store stuff
	ram_value_a = _ldabuf(instr[1], ram)
	ram_value_b = _ldabuf(instr[2], ram)
	result = ram_value_a + ram_value_b
	_stabuf(result, instr[3], ram) # saves our variable by calling STA instead of doing so by itself
	if LOG_CONSOLE: print('SUM called: ', ram_value_a, '[', instr[1], '] + ', ram_value_b, '[', instr[2], '] = ', result, '[', instr[3], ']')

def _sub(pc, instr, screen, win):
	_lda_ac(ram.data[instr[1]], cpu) # sends instr[1] to AC
	_lda_ac((cpu.ac - ram.data[instr[2]]), cpu) # adds instr[2] and stores in AC
	if LOG_CONSOLE: print('SUB called: ', ram.data[instr[1]], '[', instr[1], '] - ', ram.data[instr[2]], '[', instr[2], '] = ', cpu.ac, '.')

def __sub(instr, ram): # same issue as SUM. deprecated, but usable anyway
	ram_value_a = _ldabuf(instr[1], ram)
	ram_value_b = _ldabuf(instr[2], ram)
	result = ram_value_a - ram_value_b
	_stabuf(result, instr[3], ram) # saves our variable by calling STA instead of doing so by itself
	if LOG_CONSOLE: print('SUB called: ', ram_value_a, '[', instr[1], '] - ', ram_value_b, '[', instr[2], '] = ', result, '[', instr[3], ']')

def _subbuf(x, y, addr, ram): # SUB_BUFFER
	if LOG_CONSOLE: print('SUM called: ', x, ' - ', y, ' = ', (x - y), '[', addr, ']')
	_stabuf((x - y), addr, ram)