# prints starting art based on screen size

def print_art():
    width = get_width()
    if width >= 100:
        art = wide()
    elif width >= 60:
        art = medium()
    else:
        art = small()

    print(art)


def get_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def wide():
    return = f"""
        \033[1;36m ____                            \033[1;31m                  _ \033[0m
        \033[1;36m/ ___|  ___ _ __ __ _ _ __   ___ \033[1;31m_   _  ___  _   _| |\033[0m
        \033[1;36m\___ \ / __| '__/ _` | '_ \ / _ \\\033[1;31m | | |/ _ \| | | | |\033[0m
        \033[1;36m ___) | (__| | | (_| | |_) |  __/\033[1;31m |_| | (_) | |_| |_|\033[0m
        \033[1;36m|____/ \___|_|  \__,_| .__/ \___|\033[1;31m\__, |\___/ \__,_(_)\033[0m
        \033[1;36m                     |_|         \033[1;31m|___/               \033[0m                
    """

# use this for medium size but 
# probably not necessary since 
# people will either use either large or
# small cli
def medium():   
    return f"""
        \033[1;36m ____                            \033[1;31m                  _ \033[0m
        \033[1;36m/ ___|  ___ _ __ __ _ _ __   ___ \033[1;31m_   _  ___  _   _| |\033[0m
        \033[1;36m\___ \ / __| '__/ _` | '_ \ / _ \\\033[1;31m | | |/ _ \| | | | |\033[0m
        \033[1;36m ___) | (__| | | (_| | |_) |  __/\033[1;31m |_| | (_) | |_| |_|\033[0m
        \033[1;36m|____/ \___|_|  \__,_| .__/ \___|\033[1;31m\__, |\___/ \__,_(_)\033[0m
        \033[1;36m                     |_|         \033[1;31m|___/               \033[0m                
    """

def small():
    return "Scrapeyou! (why is your terminal so small?!)"
   