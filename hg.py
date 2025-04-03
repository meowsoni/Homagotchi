# code by meowsoni
# homagotchi is a presence monitoring clock that relies on ICMP pings
# following code is distributed under MIT Licence 3.0. Please check <Github> for more info.
# user config is in lines 74-77

import time
import datetime
import random
import subprocess
import threading
import logging
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd2in13_V4

# Configure logging to also write to a file
logging.basicConfig(
    filename='hg.log',
    level=logging.INFO,
    format='%(message)s'
)

# Initialize display
epd = epd2in13_V4.EPD()
epd.init()
epd.Clear(0xFF)

# Constants
WIDTH, HEIGHT = 250, 122
FONT_PATH = "./fonts/DejaVuSans.ttf"

# Load fonts
font_face = ImageFont.truetype(FONT_PATH, 24)
font_name = ImageFont.truetype(FONT_PATH, 14)
font_clock = ImageFont.truetype(FONT_PATH, 36)
font_date = ImageFont.truetype(FONT_PATH, 16)

# Faces used in display
faces = ["", "(◕‿‿◕)", "(◕‿◕ )", "( ◕‿◕)", "(⌐■_■)", "(■_■⌐)"]

# Logging helper
def log(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"[{timestamp}] {msg}"
    print(message)
    logging.info(message)

# User class with ping check
class User:
    def __init__(self, name, ip_address, face_index):
        self.is_animating = False
        self.name = name
        self.ip_address = ip_address
        self.face_index = face_index
        self.last_ping = datetime.datetime.now()  # Pretend they just pinged in
        self.last_left = None

    @property
    def face(self):
        return faces[self.face_index]

    @property
    def is_home(self):
        return self.last_ping and (datetime.datetime.now() - self.last_ping).total_seconds() < 600

    def update_presence(self):
        result = subprocess.run(['ping', '-c', '1', '-W', '1', self.ip_address], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            self.last_ping = datetime.datetime.now()
            log(f"{self.name} was present at {self.ip_address}")
        else:
            self.last_left = datetime.datetime.now()
            log(f"{self.name} was absent at {self.ip_address}")

# Define users
user1 = User("Siddharth", "192.168.0.44", 0)
user2 = User("Alina", "192.168.0.58", 0)
users = [user1, user2]

# Partial refresh method for time and face animation
def partial_refresh_screen():
    region_image = Image.new('1', (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(region_image)
    now = datetime.datetime.now()

    draw.text((10, 5), user1.face, font=font_face, fill=0)
    draw.text((140, 5), user2.face, font=font_face, fill=0)
    draw.text((10, 40), user1.name, font=font_name, fill=0)
    draw.text((140, 40), user2.name, font=font_name, fill=0)
    draw.text((10, 60), now.strftime("%H:%M"), font=font_clock, fill=0)
    draw.text((10, 100), now.strftime("%A %d %B"), font=font_date, fill=0)

    epd.displayPartial(epd.getbuffer(region_image))
    log("Partial refresh successful")

# Full refresh method to check for sleep condition and EPD health
def full_refresh():
    epd_awake = True  # start with the display assumed awake

    while True:
        # Prevent full refresh if any user is animating to prevent SPI contention
        if any(user.is_animating for user in users):
            time.sleep(1)
            continue

        if should_sleep(users):
            if epd_awake:
                log("No one home for 30 minutes. Putting EPD to sleep.")
                epd.Clear(0xFF)
                epd.sleep()
                epd_awake = False
        else:
            if not epd_awake:
                log("Someone has returned home. Waking EPD.")
                epd.init()
                epd_awake = True

            # Draw the screen
            image = Image.new('1', (WIDTH, HEIGHT), 255)
            draw = ImageDraw.Draw(image)
            now = datetime.datetime.now()

            draw.text((10, 5), user1.face, font=font_face, fill=0)
            draw.text((140, 5), user2.face, font=font_face, fill=0)
            draw.text((10, 40), user1.name, font=font_name, fill=0)
            draw.text((140, 40), user2.name, font=font_name, fill=0)
            draw.text((10, 60), now.strftime("%H:%M"), font=font_clock, fill=0)
            draw.text((10, 100), now.strftime("%A %d %B"), font=font_date, fill=0)

            epd.display(epd.getbuffer(image))
            log("Full refresh successful")

        time.sleep(300)

# Face animation routine
def face_animation(user):
    if should_sleep(users):
        log(f"{user.name} tried to animate, but EPD is currently waking up.")
        return

    user.is_animating = True
    log(f"{user.name} is currently animating")

    animation_sequence = [2, 3, 2, 3, 1]  # Define a specific pattern
    for idx in animation_sequence:
        user.face_index = idx
        log(f"Rendering face_index {idx} for {user.name}")
        partial_refresh_screen()
        time.sleep(0.3)
    user.is_animating = False
    log(f"{user.name} has finished animating")

# Evaluates sleep condition
def presence_within(users, seconds):
    now = datetime.datetime.now()
    return any(user.last_ping and (now - user.last_ping).total_seconds() < seconds for user in users)

def should_sleep(users):
    return not presence_within(users, 1800)

# Update routine
def update_users():
    for user in users:
        previous_ping = user.last_ping
        previously_home = user.is_home

        user.update_presence()

        # Automatically manage base face state
        if user.is_home:
            if user.face_index not in (4, 2, 3):  # Don't override 24h or animating face
                user.face_index = 1
        else:
            if user.face_index != 0:
                user.face_index = 0
                log(f"{user.name} is away. Face cleared.")

        # If user just returned home
        if user.is_home and not previously_home:
            log(f"{user.name} was newly pinged at {user.ip_address}")
            epd.init()
            time.sleep(1)

        # Check for 24-hour home achievement
        if user.is_home and user.last_left:
            time_at_home = (datetime.datetime.now() - user.last_left).total_seconds()
            if time_at_home > 86400 and user.face_index != 4:
                user.face_index = 4
                log(f"{user.name} has been home for 24h at {user.ip_address}")

        # Animate with every succesful ping
        if user.is_home and (not previous_ping or user.last_ping != previous_ping):
            log(f"{user.name} was pinged at {user.ip_address}")
            face_animation(user)

# Main loop
def main():
    threading.Thread(target=full_refresh, daemon=True).start()
    while True:
        update_users()
        time.sleep(30)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd2in13_V4.epdconfig.module_exit(cleanup=True) #cleans up all GPIO pins
        exit()
