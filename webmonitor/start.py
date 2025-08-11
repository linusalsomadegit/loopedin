
# Vlad Krstevski
# Created 8/11/2025


from webmonitor.Config import Config
from webmonitor.Menu import Menu




# entry point
def start():
    # load config
    Config.ensure_config()

    data = Config.read()
    if (data == []):
        print('Website scrape list is empty. Configure it by editing config.json file.')
        exit(0)


    menu = Menu()
    menu.interactive_gui()


if (__name__ == '__main__'):
    start()

