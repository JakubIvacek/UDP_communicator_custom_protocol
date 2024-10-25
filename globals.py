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
header_size = 12  # header format 11 + 1 padding
max_fragment_size = 1460 # IP + UDP + MINE = 40 B
