import hydra
from pygui import U2netGui


# @hydra.main(version_base=None, config_path=".", config_name="config")
@hydra.main(version_base=None, config_path=".", config_name="config-win")
def main(cfg):
    U2netGui(cfg)


if __name__ == '__main__':
    main()
