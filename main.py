import machine
import dht
from machine import Pin, Timer
import network
import urequests #req various urls
from umqtt.robust import MQTTClient
import os
import time

# the following function is the callback which is
# called when subscribed data is received
# <user-name>/feeds/gpio2

def reset_func(timer):
    machine.reset()
def internet_on():
    try:
        response = urequests.get('http://clients3.google.com/generate_204')
        if response.status_code == 204:
            return True
        elif response.status_code == 200:
            return True
        else:
            return False
    except:
        return False
look1 = 0
def call_back_routine(feed, msg):
    print('Received Data:  feed = {}, Msg = {}'.format(feed, msg))
    global look1
    if ADAFRUIT_IO_FEEDNAME1 in feed:
        action = str(msg, 'utf-8')
        if action == 'ON':
            pin16.value(1)
            look1 = 1
        else:
            pin16.value(0)
            look1 = 0
        print('action = {} '.format(action))

ADAFRUIT_IO_URL = b'io.adafruit.com' #site server
ADAFRUIT_USERNAME = b'arkajitdatta'
ADAFRUIT_IO_KEY = b'aio_mofW049HRgbiXI5TU5M6yqHzR0Zk'
ADAFRUIT_IO_FEEDNAME1 = b'water switch1'
ADAFRUIT_IO_FEEDNAME2 = b'fake2'
ADAFRUIT_IO_FEEDNAME3 = b'humidity'
ADAFRUIT_IO_FEEDNAME4 = b'temperature'
# create a random MQTT clientID
random_num = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id = bytes('client_'+str(random_num), 'utf-8')
client = MQTTClient(client_id=mqtt_client_id,
                    server=ADAFRUIT_IO_URL,
                    user=ADAFRUIT_USERNAME,
                    password=ADAFRUIT_IO_KEY,
                    ssl=False) #framework making a client connecting url
#gloabal variables
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mqtt_feedname1 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME1), 'utf-8')
mqtt_feedname2 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME2), 'utf-8')
mqtt_feedname3 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME3), 'utf-8')
mqtt_feedname4 = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, ADAFRUIT_IO_FEEDNAME4), 'utf-8')
pin16 = Pin(5, Pin.OUT)
pin16.value(0)

dht11 = dht.DHT11(Pin(14)) #specifying pin for the temperature and humidity sensor

def temp_humidity_check_send():
    time.sleep(2)
    dht11.measure() #for measuring
    temp = dht11.temperature()
    hum = dht11.humidity()
    client.check_msg()
    client.publish(mqtt_feedname3, bytes(str(hum), 'utf-8'), qos=0) #sending the humidity value
    time.sleep(5)
    client.check_msg()
    client.publish(mqtt_feedname4, bytes(str(temp), 'utf-8'), qos=0)#sending the temperature value


def do_connect():
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('arka', '12345678') #username and password of the wifi
        while not wlan.isconnected(): #wifi
            pass
    print('network config:', wlan.ifconfig())
    try:
        print("Client connection....going on.....")
        client.connect()
        client.set_callback(call_back_routine) #call back
        client.subscribe(mqtt_feedname1)
        client.subscribe(mqtt_feedname2)
        client.subscribe(mqtt_feedname3)
        client.subscribe(mqtt_feedname4)
        print("Client Connection Completed!")
    except Exception as e:
        print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
        if (not internet_on()):
            print("No internet")
            time.sleep(15)
            machine.reset()
        else:
            machine.reset()

#Reset After Every 2 hours ----
flash = Timer(-1)
flash.init(period=7200000, mode=Timer.PERIODIC, callback=reset_func)


def main():
    wlan = network.WLAN(network.STA_IF) #hotspot
    wlan.active(True)
    pin16.value(0)
    while True:
        if not wlan.isconnected():
            print("Was not connected! ... Connecting....1")
            do_connect()
        if not internet_on():
            print("No internet")
            time.sleep(15)
            machine.reset()
        time.sleep(5)
        if wlan.isconnected() and internet_on():
            try:
                client.check_msg() #call back routine
                if look1 == 1:
                    client.publish(mqtt_feedname2, bytes(str("100"), 'utf-8'), qos=0)
                elif look1 == 0:
                    client.publish(mqtt_feedname2, bytes(str("0"), 'utf-8'), qos=0)
            except:
                if not wlan.isconnected():
                    print("Was not connected! ... Connecting....3")
                    do_connect()
                if not internet_on():
                    print("No internet----1")
                    time.sleep(15)
                    machine.reset()

        time.sleep(10)

        if wlan.isconnected() and internet_on():
            try:
                temp_humidity_check_send()
            except:
                if not wlan.isconnected():
                    print("Was not connected! ... Connecting....3")
                    do_connect()
                if not internet_on():
                    print("No internet----1")
                    time.sleep(15)
                    machine.reset()

if __name__ == '__main__':
    main()