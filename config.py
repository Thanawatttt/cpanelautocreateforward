import configparser
import random

config_file = "config.conf"

config = configparser.ConfigParser()
config.read(config_file)

# CPanel config
cpanel_user = config["cpanel"]["user"]
cpanel_token = config["cpanel"]["token"]
cpanel_host = config["cpanel"]["host"]
domain = config["cpanel"]["domain"]

# Email config
forward_to_email = config["email"]["forward_to"]
prefixes = [p.strip() for p in config["email"]["prefixes"].split(",")]

# Server config
server_port = int(config["server"]["port"])

# Helper for random prefix placement
def generate_email_username(length=8):
    rand = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=length))
    prefix = random.choice(prefixes)
    if random.choice([True, False]):
        return f"{prefix}-{rand}"
    else:
        return f"{rand}-{prefix}"
