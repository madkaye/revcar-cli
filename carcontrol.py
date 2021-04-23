import time
from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, Characteristic, ScanEntry, Service, UUID
from knowncars import *

BTDRIVE_HANDLE  = 0x0017
BTCMD_HANDSHAKE = [b'\x16',
                   b'\x91\x01',
                   b'\x84\x04',
                   b'\x79',
                   b'\x91\x01',
                   b'\x19',
                   b'\x91\xFF',
                   b'\x14']
BTCMD_FIREGUN   = b'\x95\x00\x04\x01'
BTCMD_DRIVE     = 0x78

class MainDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        print("handleDiscovery: Device {} (Type: {}, New Device: {}, New Data: {})\r".format(dev.addr, dev.addrType,
                                                                                           isNewDev, isNewData))

    def handleNotification(self, cHandle, data):
        print("handleNotification: Handle {} ({:02x} - Data: {:02x})\r".format(cHandle, cHandle, data))


class CarControl:
    scanner = None
    devices = []
    devicetext = ""
    isConnected = False
    carAddr = None
    carName = None
    carDevice = None
    carPeripheral = None
    
    def __repr__(self):
        return "devices: {}, address: {}, carName: {}".format(len(self.devices),
                                                             self.carAddr, self.carName)
        #return "devices: {}".format(len(self.devices))

    def scan(self, timeout=10):
        foundDevices = 0
        self.devices = []
        self.devicetext = ""

        newdevices = []
        scansuccess = False
        try:
            self.scanner = Scanner()
            self.scanner.withDelegate(MainDelegate())
            newdevices = self.scanner.scan(timeout)
            scansuccess = True
        except Exception as e:
            scansuccess = False
        
        if scansuccess:
            for dev in newdevices:
                if dev.addrType == btle.ADDR_TYPE_PUBLIC:
                    foundDevices = foundDevices + 1
                    self.devices.append({"name": dev.getValueText(9), "addr": dev.addr})
                    self.devicetext = self.devicetext + "> Device #{} {} ({}), [{}], [{}]\n".format(foundDevices,
                                                          dev.addr, dev.addrType, dev.getValueText(9), dev.getValueText(8))

        # add known cars
        for k in KNOWN_CARS:
            foundDevices = foundDevices + 1
            self.devices.append({"name": k["name"], "addr": k["addr"]})
            self.devicetext = self.devicetext + "> Device #{} {} ({}), [{}]\n".format(foundDevices,
                                                  k["addr"], "Known Device", k["name"])
            

        return scansuccess

    def connect(self, carnum):
        
        if len(self.devices) == 0:
            print("connect: Nothing scanned")
            return
        
        if carnum < 0 or carnum > len(self.devices):
            print("connect: Car number invalid, {}".format(carnum))
            return
        
        try:
            self.carAddr = self.devices[carnum]["addr"]
            self.carName = self.devices[carnum]["name"]
            self.carPeripheral = Peripheral()
            self.carPeripheral.withDelegate(MainDelegate())
            self.carPeripheral.connect(self.carAddr)
            self.isConnected = True
            return True

        except Exception as e:
            self.carPeripheral = None
            print("connect: Error,", e)
            return False


    def listdescriptors(self):
        try:
            print("listdescriptors: ...")
            print("listdescriptors: listing descriptors")
            descriptors = self.carPeripheral.getDescriptors()
            for desc in descriptors:
                print("   --  DESCRIPTORS: {}, [{}], Handle: {} (0x{:04x})".format(desc.uuid, UUID(desc.uuid).getCommonName(),
                                                                                   desc.handle, desc.handle))
        except Exception as e:
            print("listdescriptors: Error,", e)

    def listservices(self):
        try:
            print("listservices: listing services")
            services = self.carPeripheral.getServices()
            for serv in services:
                print("   -- SERVICE: {} [{}]".format(serv.uuid, UUID(serv.uuid).getCommonName()))
                characteristics = serv.getCharacteristics()
                for chara in characteristics:
                    print("   --   --> CHAR: {}, Handle: {} (0x{:04x}) - {} - [{}]".format(chara.uuid,
                                                                                    chara.getHandle(),
                                                                                    chara.getHandle(),
                                                                                    chara.propertiesToString(),
                                                                                    UUID(chara.uuid).getCommonName()))
        except Exception as e:
            print("listservices: Error,", e)

    def disconnectcar(self):
        self.isConnected = False
        
        if self.carPeripheral is None:
            print("disconnectcar: No car connected")
            return False
        
        try:
            self.carPeripheral.disconnect()
            self.carPeripheral = None
            return True
        except Exception as e:
            print("disconnectcar: Error,", e)
            return False

    def readcharacteristics(self):
        try:
            if self.carPeripheral is None:
                print("readcharacteristics: No car connected")
                return
            print("readcharacteristics: reading the readables")

            chars = self.carPeripheral.getCharacteristics()
            for c in chars:
                if c.supportsRead():
                    print("  -- READ: {} [{}] (0x{:04x}), {}, Value: {}".format(c.uuid, UUID(c.uuid).getCommonName(),
                                                                                c.getHandle(), c.descs, c.read() if c.supportsRead() else ""))
        except Exception as e:
            print("readcharacteristics: Error,", e)

    def writevalue(self, handle, value, wait=False):
        try:
            if self.carPeripheral is None:
                #print("writevalue: No car connected")
                return
            #print("writevalue: writing to handle 0x{:04x} value {}".format(handle, value))

            self.carPeripheral.writeCharacteristic(handle, value, wait)

        except Exception as e:
            print("writevalue: Error,", e)

    def readvalue(self, handle):
        try:
            if self.carPeripheral is None:
                print("readvalue: No car connected")
                return
            print("readvalue: reading handle 0x{:04x}".format(handle))
            value = self.carPeripheral.readCharacteristic(handle)
            print("readvalue: Handle 0x{:04x} = {}".format(handle, value))

        except Exception as e:
            print("readvalue: Error,", e)

    def sendhandshake(self):
        # handshake...
        for finger in BTCMD_HANDSHAKE:
            self.writevalue(BTDRIVE_HANDLE, finger, True)

    def carfiregun(self, intensity=0.5):
        self.writevalue(BTDRIVE_HANDLE, BTCMD_FIREGUN)

    def carforward(self, intensity=0.5):
        if intensity < 0.1 or intensity > 1:
            return
        scale = 0x1F
        actual_intensity = 0x00 + round(scale * intensity)

        # pull value list
        tx_list = [BTCMD_DRIVE, actual_intensity, 0x00]
        tx_data = bytes(tx_list)
        self.writevalue(BTDRIVE_HANDLE, tx_data, True)

    def carreverse(self, intensity=0.5):
        if intensity < 0.1 or intensity > 1:
            return
        scale = 0x1F
        actual_intensity = 0x20 + round(scale * intensity)

        # pull value list
        tx_list = [BTCMD_DRIVE, actual_intensity, 0x00]
        tx_data = bytes(tx_list)
        self.writevalue(BTDRIVE_HANDLE, tx_data, True)

    def carright(self, intensity=0.5):
        if intensity < 0.1 or intensity > 1:
            return
        scale = 0x1F
        actual_intensity = 0x40 + round(scale * intensity)

        # pull value list
        tx_list = [BTCMD_DRIVE, 0x00, actual_intensity]
        tx_data = bytes(tx_list)
        self.writevalue(BTDRIVE_HANDLE, tx_data, True)

    def carleft(self, intensity=0.5):
        if intensity < 0.1 or intensity > 1:
            return
        scale = 0x1F
        actual_intensity = 0x60 + round(scale * intensity)

        # pull value list
        tx_list = [BTCMD_DRIVE, 0x00, actual_intensity]
        tx_data = bytes(tx_list)
        self.writevalue(BTDRIVE_HANDLE, tx_data, True)

