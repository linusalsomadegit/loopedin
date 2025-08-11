

import sys
import os

if os.name == 'nt':
    import msvcrt
else:
    import tty, termios

from webmonitor.Scheduler import Scheduler
from webmonitor.Config import Config



def get_key():
    if os.name == 'nt':  # Windows
        return msvcrt.getch().decode()
    else:  # Unix (macOS, Linux)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)



class Menu:
    def interactive_gui(self):
        self.status_menu()
        
        while True:

            key = get_key().lower()
            match key:
                case 'q':
                    return print('Quitting.')
                case 'h':
                    self.display_help()
                case 'i':
                    self.display_info()
                case 'b':
                    Scheduler.start()
                    print("Scheduler service started.\n")
                case 'e':
                    Scheduler.stop()
                    print("Scheduler service stopped.\n")
                case 's':
                    self.status_menu()
                case 'w':
                    site_list = Config.websites_only()
                    if (not site_list):
                        print('No websites added.')
                    else:
                        print("List of added websites:")
                        [print(site) for site in site_list]
                        print()
                case _:
                    print(f"Unknown option: {key}. Press h to view the help page.")

    def display_help(self):
        print("""
        Help Manual
        s       Displays the status menu.
        h       Displays this menu.
        i       Displays additional info about this program.
        q       Stop all scheduled tasks and quit.

        b       Begin the background scraping service.
        e       Ends the background scraping service.
        
        w       Lists all the websites in the configuration.
        """)

    def display_info(self):
        print("The additional info page will live here in the future.\n")

    def status_menu(self):
        is_system_on = Scheduler.running

        print(f"""
        Webmonitor tool for tracking website changes across time.
        To access the help menu press h. Press q to quit.
        Monitoring Website Changes: {is_system_on}
        """)