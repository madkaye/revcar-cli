
RevCar - Command Line Interface 
===============================

This is a test CLI application for controlling WowWee RevCar devices through Bluetooth Low Energy (BLE) built in Python using Bluepy for BLE control and curses for display and keyboard input.

This has been tested on Linux and depends on *bluepy* - so most likely won't run on Windows

Usage
-----
1. Install `python3`, `pip3`
2. Install `bluepy` using pip3: `pip3 install bluepy`
3. Mark revcar-cli.py as executable: `chmod +x revcar-cli.py`
4. Run the app with sudo to enable BLE scanning: `sudo ./revcar-cli.py`
5. If you prefer not to run the app with sudo, find out the MAC addresses of 
   your cars, then add them to the `knowncars.py` file



Protocol
--------
The protocol used here is pretty simple for the most part. The app scans for RevCar devices and measures the RSSI expected to sense the phone being swiped near the car (as there are usually 2 of them) and then connects to it.

After the connection is established:
- Remote app will enumerate all the services and characteristics
- Sends a handshake code (this is to setup the car's *character*: speed, accuracy, etc.)
- Setups up a notification handle (through 0x14 for notify on 0x12) - this is likely for the *hit* events from the other car (haven't been able to get this working)
- Then it's ready for driving and firing commands over handle 0x17.
  - Driving is usually a 3-byte sequence starting with 0x78
  - Firiing is a static 4-byte sequence


A sample packet capture of the GATT commands and events is in the file `btsnoop_hci.log` where *localhost* is the driving application and *remote* is the RevCar device.

Here is a sample of the attributes advertised by the car:
```
   -- SERVICE: 00001800-0000-1000-8000-00805f9b34fb [Generic Access]
   --   --> CHAR: 00002a00-0000-1000-8000-00805f9b34fb, Handle: 3 (0x0003) - READ WRITE  - [Device Name]
   --   --> CHAR: 00002a01-0000-1000-8000-00805f9b34fb, Handle: 5 (0x0005) - READ  - [Appearance]
   --   --> CHAR: 00002a04-0000-1000-8000-00805f9b34fb, Handle: 7 (0x0007) - READ  - [Peripheral Preferred Connection Parameters]
   -- SERVICE: 00001801-0000-1000-8000-00805f9b34fb [Generic Attribute]
   -- SERVICE: 0000180a-0000-1000-8000-00805f9b34fb [Device Information]
   --   --> CHAR: 00002a23-0000-1000-8000-00805f9b34fb, Handle: 11 (0x000b) - READ  - [System ID]
   --   --> CHAR: 00002a26-0000-1000-8000-00805f9b34fb, Handle: 13 (0x000d) - READ  - [Firmware Revision String]
   --   --> CHAR: 00002a29-0000-1000-8000-00805f9b34fb, Handle: 15 (0x000f) - READ  - [Manufacturer Name String]
   -- SERVICE: 0000ffe0-0000-1000-8000-00805f9b34fb [ffe0]
   --   --> CHAR: 0000ffe4-0000-1000-8000-00805f9b34fb, Handle: 18 (0x0012) - NOTIFY  - [ffe4]
   -- SERVICE: 0000ffe5-0000-1000-8000-00805f9b34fb [ffe5]
   --   --> CHAR: 0000ffe9-0000-1000-8000-00805f9b34fb, Handle: 23 (0x0017) - WRITE NO RESPONSE WRITE  - [ffe9]
   -- SERVICE: 0000ffa0-0000-1000-8000-00805f9b34fb [ffa0]
   --   --> CHAR: 0000ffa1-0000-1000-8000-00805f9b34fb, Handle: 27 (0x001b) - READ NOTIFY  - [ffa1]
   --   --> CHAR: 0000ffa2-0000-1000-8000-00805f9b34fb, Handle: 30 (0x001e) - READ WRITE  - [ffa2]
   -- SERVICE: 0000ff90-0000-1000-8000-00805f9b34fb [ff90]
   --   --> CHAR: 0000ff91-0000-1000-8000-00805f9b34fb, Handle: 33 (0x0021) - READ WRITE  - [ff91]
   --   --> CHAR: 0000ff92-0000-1000-8000-00805f9b34fb, Handle: 35 (0x0023) - READ WRITE  - [ff92]
   --   --> CHAR: 0000ff94-0000-1000-8000-00805f9b34fb, Handle: 37 (0x0025) - WRITE  - [ff94]
   --   --> CHAR: 0000ff95-0000-1000-8000-00805f9b34fb, Handle: 39 (0x0027) - READ WRITE  - [ff95]
   --   --> CHAR: 0000ff97-0000-1000-8000-00805f9b34fb, Handle: 41 (0x0029) - READ WRITE  - [ff97]
   --   --> CHAR: 0000ff98-0000-1000-8000-00805f9b34fb, Handle: 43 (0x002b) - READ WRITE  - [ff98]
   --   --> CHAR: 0000ff9b-0000-1000-8000-00805f9b34fb, Handle: 45 (0x002d) - WRITE  - [ff9b]
   --   --> CHAR: 0000ff9c-0000-1000-8000-00805f9b34fb, Handle: 47 (0x002f) - READ WRITE  - [ff9c]
   -- SERVICE: 0000ff30-0000-1000-8000-00805f9b34fb [ff30]
   --   --> CHAR: 0000ff31-0000-1000-8000-00805f9b34fb, Handle: 50 (0x0032) - WRITE  - [ff31]
   -- SERVICE: 0000ff10-0000-1000-8000-00805f9b34fb [ff10]
   --   --> CHAR: 0000ff1b-0000-1000-8000-00805f9b34fb, Handle: 53 (0x0035) - READ WRITE  - [ff1b]
```


TODO
----
* Avoid scanning when a car is connected (or disconnect first)
* Handle 'hit' events through BLE notifications on handle 0x12 or 0x14


