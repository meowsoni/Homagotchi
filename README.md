# Homagotchi
Homagotchi is a presence monitoring clock that tells who is 'home' using ICMP pings.

![homagotchi_screen_preview](https://github.com/user-attachments/assets/40828fba-221f-4096-a65a-758b7abf45f4)

Written for Waveshare 2.13' ePaper HAT v4 and Raspberry Pi Zero 2w, this Python program pings a user's smartphone (or any other device) to ascertain that they are home by showing a little ASCII face (◕‿‿◕).

If a ping is succesful their face does a lively animation: ( ◕‿◕) (◕‿◕ ).

If they don't leave home for 24h they get a cool face: (⌐■_■).

# Features
Homagotchi debounces transient network issues by polling for properties like `is_home` and `last_ping` which change only when a user has not responded to a ping in over 10 minutes.

It takes care of the health of your e-Paper screen by running a thread that refreshes the screen fully every 4 minutes. The same thread evaluates if none of the users have responded to a ping in over 30 minutes, and if so it cleans all pixels and puts the screen to sleep. The screen wakes up only when one of the users respond to a ping.

The program writes logs to a file and is currently programmed to delete all previous logs upon boot.

Although I have not tested, the script should be compatible with all Waveshare EPDs. Just change `WIDTH` and `HEIGHT` properties and redraw the interface using `Pillow` as I have done in the script `hg.py`. Same goes for adding more users; if you have a bigger screen (or happy to sacrifice clock) you can add more faces by adding a line for each user in the script.

**Bear in mind**<br>
Homagotchi does not ping users simultaneously but consecutively to avoid SPI lockup when calling for e-Paper display to refresh.
When you switch on the device, it assumes all users are home, so it may take up to 10 minutes to start showing accurate data.

Free to use, without guarantees.
