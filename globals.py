# ----
# -------  GLOBAL VARIABLES
keep_alive_running = True
user_input = ""
on = True
switch = False
transfer = False
file = False
transfer_file = False
sender = False
header_format = "BHHHHH"
header_size = 8  # header format 7 + 1 padding
max_fragment_size = 1464 # IP + UDP + MINE = 36 B
