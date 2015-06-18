Introduction
============

The Internet of Things (IoT) is a paradigm where many “things”, embedded
with sensors, exchange data with one another and/or a central hub to
provide a common service or application. As IoT devices and
applications grow in popularity, there is a need for a common source of
time. Applications such as coordinated audio playback, video monitoring,
and reading sensor data all process time-stamped data, and there is a
need for time-stamps from one node to align with time-stamps on a
different node. However, the embedded devices that timestamp this data
do not have highly accurate sources of time, as it is cost-prohibitive
and often impractical to have more precise clocks. Additionally, these
devices often have small batteries and slow microprocessors, meaning
they cannot devote much time to time synchronization.

Time synchronization of wireless nodes is an active area of research.
While there are many solutions available, time synchronization solutions
using *commercially available radio technology* such as Wi-Fi or
Bluetooth LE are less common. Some solutions, such as Flooding Time
Synchronization Protocol use platforms dedicated
specifically for research, such as the Mica2 mote. Other solutions, such
as the Sonos SonosNet, use a proprietary wireless networking technology.
In order for IoT to become fully realized, manufacturers need to be able
to leverage existing, open wireless standards. This will enable
manufacturers to create devices that interoperate with one another,
using commercial off-the shelf (COTS) hardware.

In this paper, I will discuss BlueSync, a time synchronization protocol
built on top of open standards, with no proprietary technology.

Existing Solutions
==================

In this section, I will outline some existing solutions and contrast
them with Bluesync.

Sonos SonosNet
--------------

![The Sonos Play:3 Player, as featured on on the Sonos
website.[fig:sonos-play-3]](assets/play3-pair-vert.png)

Sonos is a company that specializes in wirelessly connected whole-home
audio solutions. When a consumer installs multiple Sonos players in her
home, she can stream music to any player in the house, or even play
music in one (or all) zones simultaneously. The players accomplish this
via SonosNet, a proprietary wireless protocol that builds a mesh network
throughout the house.

The Sonos devices do use COTS 802.11 radios—the Sonos Play:3 All-in-One
system (shown in Figure [fig:sonos-play-3]) contains a Qualcomm Atheros
wireless card, and the system utilizes multiple-input, multiple-output
(MIMO) technology. Sonos does not offer an official
API for interacting with its speakers. However, many projects provide
unofficial APIs that can perform network discovery and control speakers
within the network. In short, while Sonos intends to keep
SonosNet closed, it is quite easy for 802.11 devices to gain
(unauthorized) access to the network of players.

Further, when using SonosNet, at least one device in the network needs
to have a wired connection to the internet, so that it can become an
uplink for the remaining nodes in the network. This device can either be
a speaker or a bridge (a dedicated network node). Recently, Sonos
introduced the option to use an existing WiFi network in a home instead
of SonosNet, but this configuration does have some limitations, and the
company does stress that performance is dependent on WiFi broadcast
strength.

Though SonosNet is a proven, commercially viable networking solution, it
does have drawbacks that would prevent it from becoming a broadly used
IoT solution. SonosNet is a proprietary technology, and there appear to
be no plans for Sonos to license it to other manufacturers. Apart from
this business consideration, technical limitations exist. The protocol
does not appear to allow for duty-cycling, as nodes must keep an active
WiFi connection at all times. Further, it does not
appear that SonosNet can "channel-hop"—the system will settle on
2.4GHz channel 1, 6, or 11. Customers report needing to manually change
channels in the face of interference on a single channel:online.
Lastly, the 802.11 protocol is generally unsuitable for IoT devices, due
to poor energy awareness and added bill of materials (BoM) cost.

Flooding Time Synchronization Protocol (FTSP)
------------------------------

Maróti et al describe the Flooding
Time Synchronization Protocol (FTSP) as a protocol intended to provide time
synchronization for multihop wireless sensor networks (WSNs). It accomplishes this by
cleverly timestamping and estimating delay in interrupt handling,
encoding, propagation, and decoding. Additionally, FTSP can estimate the
clock drift and handle changes in topology.

FTSP works by timestamping a message at both the sender and receiver. In
order to generate its timestamps, the sender notes the time at which
each byte of payload data gets transmitted, and combines the data
together into a single, corrected timestamp that eliminates jitter in
channel access and interrupt handling. The receiver further corrects
this timestamp by calculating the byte alignment time as it reassembles
the message.

While FTSP is quite robust and accurate (within tens of microseconds),
some challenges persist. Maróti et al implemented FTSP on
the Mica2 mote platform, a popular choice for research and development.
However, the Mica2 has yet to gain traction in commercial applications.
Additionally, FTSP displays high complexity, and requires software
embedded in the MAC layer of the device—a requirement that may be
problematic for manufacturers of IoT devices.

BlueSync Operation
==================

In this section, I will outline some of the key concepts that underlie
BlueSync.

Reference Broadcast Synchronization
-----------------------------------

![A flowchart showing how reference broadcast synchronization (RBS) can
help nodes determine their offsets against a reference
clock.[fig:rbs-flowchart]](assets/rbs-flowchart.png)

Reference Broadcast Synchronization (RBS) is a time synchronization
technique where nodes locally timestamp a common, observed event (i.e.
broadcast. Figure [fig:rbs-flowchart] briefly
describes the process of time synchronization.

RBS requires a wireless network with a common broadcast channel. The two
important roles in an RBS system are the *reference node* and the
*broadcast node*. The broadcast node is responsible for sending out the
broadcast event that all other nodes synchronize off of, and the
reference node is the node whose clock is considered the one true
picture of time i.e. all data timestamps are relative to its clock.

When the broadcast node emits its broadcast, all nodes who hear it will
timestamp its arrival relative to its own clock. Note that due to clock
drift, booting up at different times, etc, devices will not necessarily
have the same timestamp. However, all timestamps will refer to the same
*event*. After the broadcast event, nodes will exchange messages to
determine their offset from the reference node.

A few key assumptions underlie RBS. First is that all nodes *hear the
same broadcast*. If a node misses a broadcast due to a collision or
interference, it may erroneously submit an old timestamp from a previous
broadcast, and thus calculate a large offset from the reference node.
This can be mitigated with the use of a sequence number to help nodes
identify one broadcast from the next. Second, it assumes the all nodes
hear the same broadcast *at the same time*. This is an important
distinction—many wireless protocols retransmit broadcasts multiple times
in a row. If the period of the retransmission is low, this can be deemed
acceptable error.

Bluetooth Low Energy
--------------------

BlueSync utilizes the Bluetooth Low Energy (BLE) wireless standard for
its communications. Originally developed by Nokia as Wibree, the
standard is intended for low-power sensor applications
[Chapter 2]. BLE has recently seen a huge uptick in popularity, becoming
available in most smartphones and tablets. Additionally, many
BLE-enabled sensors are now available. This is a huge differentiator for
BLE in the IoT space—other standards such as ZigBee and Z-Wave do not
enjoy

The core aspects of BLE are *connectionless operation* and *the generic
attibute profile*, also known as GATT. Connectionless operation implies
that devices do not keep any state for individual connections. The GATT
server is a service-based abstraction of data that can be written to or
read from a BLE device.

A GATT server is composed of one or more *services*. Each service has a
distinct set of *characteristics*, each labelled with a universally
unique identifier (UUID). Services may contain other services, allowing
for a composition of a complex application from basic, widely accepted
components. The GATT abstraction provides a great deal of openness—any
device that implements the BlueSync service in its GATT server can take
part in BlueSync synchronization.

In BLE, devices fall into one of two groups *masters* and *slaves*.
Rather confusingly, masters are traditionally clients, and slaves are
servers. Common examples of master devices include smartphones, tablets,
home automation hubs, etc. Slaves often come in the form of sensors and
actuators (e.g. heart-rate monitor, light switch, etc). Broadcasts in
BLE are known as *advertisements*. Slaves use advertisements to
advertise themselves and any services they provide, and masters scan for
these advertisements.

These roles are quite stringent—a master cannot emit advertisements, nor
can a slave scan for them. In order for BlueSync to emit its reference
broadcast, all devices need to switch roles. That is, the master (hub)
must become a slave, and the slaves (sensors) must all become masters.
Once the broadcast event completes, all devices swap roles again.

BlueSync Protocol
=================

In this section, I will outline the specifics of the Bluesync protocol,
including the scanning, broadcasting, and sensing phase.

Overview
--------

The BlueSync protocol has multiple components at work. I will discuss
each component briefly before describing the various phases of
operation.

### BlueSync Hub

The BlueSync Hub is the device responsible for communicating with all
sensors. It discovers devices, initiates the synchronization process,
and triggers the reference event. In my experiment, the hub was a
Raspberry Pi running Raspbian Linux with a BlueGiga BLED112 USB dongle.
It also connected to a mbed via USB that would serve as the event source
(see below). Additionally, the hub contains the information needed to
correct the timestamps from BlueSync sensors.

### BlueSync Sensor

The BlueSync Sensor is the endpoint of the BlueSync system. There are 3
components to the sensor: a clock, a BLE radio, and a data capture
mechanism. The clock is fed from a onboard hardware timer. The BLE radio
enables the sensor to receive communications from the BlueSync hub
(including advertisements). Lastly, the sensor captures the timestamp of
a specific event (see below). In my experiment, the sensor was a mbed
LPC1768 microcontroller linked to a BLE112 Bluetooth LE module via UART.
The mbed’s row of LED lights forms the status panel for the sensor, and
conveys the state of the sensor.

### Event Source

In order to evalutate the accuracy of BlueSync, we need all sensors to
observe a common *event*, and timestamp it relative to their own clocks.
The BlueSync hub will attempt to correct timestamps at all the sensors
using the synchronization and compare them to the timestamp at the
reference node. The error in the synchronization is the difference
between the corrected timestamp and the reference timestamp. In my
experiment, the "event" was raising a general purpose input/output
(GPIO) pin on all BlueSync sensors simultaneously. The event came from
an mbed LPC1768 microcontroller, controlled by a Raspberry Pi via USB.

Scanning
--------

In scanning mode, the BlueSync hub listens for advertisements. BLE
advertisement packets can include up to 30 octets of data, including TX
power, discoverability/connectability, and manufacturer data. Sensors
capable of synchronization via BlueSync will include a specific
manufacturer data string within their advertisements. Upon recieving an
advertisement, the BlueSync hub will check the payload for the
manufacturer data string. If there is a match, the hub will add an entry
for the device in its *scan list*. The entry in the scan list contans
the device address, and a timestamp (relative to the the Hub’s internal
clock) when the hub received the advertisement.

Periodically, the hub will check its scan list and determine if any
devices have a timestamp older than a specific threshold, and marks them
as "lost". A lost device will be removed from the scan list. This
allows BlueSync to adapt as BLE devices come in and out of range of the
Hub.

Synchronizing
-------------

When the hub is ready to perform a synchronization event, it must first
place all sensors into master mode, so that they may begin scanning. It
accomplishes this by writing to a specific "trigger scanning"
attribute within the BlueSync profile on each sensor. When a sensor
recieves a write to this specific attribute, it notifies the mbed (which
updates the LED status panel) and begins scanning for advertisements.
Much like the hub, the sensors are looking for a specific string of
manufacturer data within the advertisement. Note this string is distinct
from the one sensors use in their own advertisements.

Once the BLE112 module matches adverising data on an incoming
advertisement to the expected data string, it will immediately raise one
of its GPIO pins, wired to a capture pin on the mbed LPC1768, allowing
the microcontroller to timestamp the event. Additionally, the module
will stop scanning for advertisements, and return to slave mode. Note
that after 5 seconds, the sensor will stop advertising and return to
master mode, regardless of whether or not an advertisement was recieved.
Once the BLE112 returns to slave mode, it notifies the mbed, so that it
can update the LED status panel.

In addition to the identifying manufacturer data, the hub includes a
*sequence number*, a unique number referencing the specific
synchronization event. The BLE112 will store this number in a
"sequence number“ attribute, so the hub can determine whether or not
a sensor heard the most recent synchronization event. In order to
recover the timestamp from the mbed, the BLE112 sends a request via the
UART link to the mbed, which responds with a 32-bit timestamp value. The
BLE112 then writes this value to a "timestamp” value.

After emitting the advertisements, the hub will go quiet, waiting for
all sensors to return to slave mode. The hub will then read attributes
from each sensor. If the sensor serving as the reference node fails to
hear the last broadcast (i.e. its reported sequence number does not
match the one the hub most recently used), the hub aborts the
synchronization attempt and tries again on the next synchronization
round. However, if the reference node does report the correct sequence
number, the hub calculates offsets for all remaining synchronizable
sensors against the reference node’s timestamp, and saves these offsets.

Sensing
-------

As part of the evaluation, the hub triggered events after 10, 30, 60,
and 500 seconds. For each event, the hub sends a signal over USB to an
mbed LPC1768, which in turn raises one of its GPIO pins. This pin is
connected to a capture pin on each of the sensor mbed units, as well as
a second interrupt pin. When the signal on this GPIO pin goes high, each
sensor mbed will timestamp the event, and the interrupt pin will prompt
it to read the capture register for the timestamp. The mbed will then
transmit this timestamp to the BLE112, which in turn will store the
timestamp in a "reference timestamp" attribute.

After triggering the event, the hub will read the "reference
timestamp“ attribute from each sensor that synchronized on the previous
broadcast. It will then "correct” timestamps from sensors using the
offsets obtained, and compare them against the reference node. BlueSync
then notes the error in measurment i.e. the difference between the
corrected timestamp and the reference node’s timestamp.

Experiment Setup
================

In this section, I will detail my experiment setup and hardware used.

Overview
--------

![A block diagram showing the BlueSync experiment layout. Note that the
BlueSync hub and the Event Source are both wired into capture pins on
the mbed units.[fig:bluesync-blocks]](assets/bluesync-blocks.png)

Figure [fig:bluesync-blocks] shows a block diagram highlighting
all the components involved in the BlueSync experimental setup. I
prototyped the full system on a single breadboard, and used 3.3V and 5V
power from an ATX power supply connected to a benchtop power supply to
power the rails on the breadboard.

Mbed LPC1768 Microcontroller
----------------------------

![The mbed LPC 1768
microcontroller.[fig:mbed-controller]](assets/mbedlpc1768.jpg)

The mbed LPC1768 microcontroller (figure [fig:mbed-controller]) is an
ideal platform for IoT applications. It is based on the NXP LPC1768 ARM
Cortex Processor. For this project, we utilized the hardware UART
controller and the on-board timer peripheral. The UART controller
allowed the mbed to communicate with its BLE radio, and the hardware
timer enabled the use of capture pins for more accurate timestamping.

Instead of timestamping on an interrupt within software, the capture
pins perform the timestamping in hardware, copying the value of the
timer counter into a specifc capture register. By configuring an
interrupt on a pin tied to the capture pin, we can read the timestamp in
software. This avoids the unpredictable delay that one can experience
with interrupts—if the processor is running in a critical section of
code where interrupts are disabled, the interrupt handler will not
immediately execute, and the timestamping will suffer from inaccuracy.

Additionally, the mbed provides 4 LEDs, which allow the device to
communicate rudimentary status. Further, the on-board USB connector also
hosts a virtual COM port that lets it communicate with a PC via a serial
connection. We use this feature inside BlueSync for debugging, and for
controlling the mbed when triggering reference events.

BlueGiga BLE112 Bluetooth LE Module
-----------------------------------

The BlueGiga BLE112 Bluetooth LE module is a BLE module designed for use
in accessories and sensors where low power consumption is important. In
addition to a BLE radio and integrated antenna, the device includes a
Texas Instuments 8051 microcontroller, complete with 8kB RAM and 128kB
Flash memory. BlueGiga maintains BGScript, a proprietary interpreted
scripting language, for use in developing BLE applications on the
BLE112. Using BGScript, one can develop directly on the BLE112 without
the use of an external microcontroller.

In BlueSync, the bulk of the code running on the sensor platform is a
BGScript program. This program handles writing attributes, scanning for
advertisements, and retrieving timestamps from the mbed.

BlueGiga BLED112 USB Dongle
---------------------------

Another BlueGiga product, the BLED112 is based off of the same chipset
as the BLE112 module, just in a USB form factor. The dongle opens up a
virtual COM port and supports a serial protocol named BGAPI, enabling
software running on a PC to communicate with BLE devices. The BlueSync
Hub uses an unofficial Python2 implementation of the protocol called
bglib:online.

Raspberry Pi Model B+
---------------------

The Raspberry Pi is single-board computer based on the Broadcom BCM
system on a chip (SoC) family. Since its debut in 2012, it has rapidly
become an ideal platform for many embedded products. In BlueSync, the
hub is implemented by a Raspberry Pi Model B+, connected to a BLED112
Bluetooth USB dongle and an mbed LPC1768 via USB.

Results
=======

In testing, BlueSync performed admirably well—on many runs, the system
detected zero error i.e. the error was less than the millisecond
resolution available on the timers. Additionally, the clock on the mbed
microcontroller is quite stable, allowing for a low duty cycle of
synchronization.

However, the solution is not particularly robust. When tested in a noisy
environment (i.e. many BLE devices operating in close proximity),
communication between the hub and sensors can time out, causing the
hub’s software to hang. Packet collisions can prevent scanners from
hearing advertisements, and the channel hopping behavior of BLE where
scanners alternate between three advertising channels can cause a time
delay between individual sensors receiving the advertisement.

Future work on BlueSync should focus on the following areas:

##### More robust connection management.

The BlueSync hub implementation I wrote for this experiment was very
basic, and worked in low-noise environments. However, in a noisy
environment, the connection management and service discovery components
of the software would hang because of a timeout in the software.
BlueSync would benefit from a hub application better written to handle
connection timeouts and lost packets between the hub and sensor.

##### Utilize advertisements for sharing timestamp and reference data.

In addition to making the connection management more robust, steps can
be taken to limit the number of connections that need to be made to the
sensors. Instead of reading data off of attributes, BlueSync sensors
could embed the most recent timestamp, sequence number, and event timing
in their advertisements, allowing the hub to retrieve information simply
by scanning for broadcasts.

##### Increase resolution of timer.

In the experiments I ran, the timer operated at a 1 millisecond
resolution. Further experimentation would use a higher-resolution timer,
in order to better characterize the system’s performance.

##### Synchronize scanners to prevent loss of advertisements due to channel hopping.

In order to make BLE more resistant to interference from other 2.4GHz
technologies (including WiFi), scanners alternate between 3 different
advertising channels. Additionally, advertising slaves can choose to
broadcast on one, two, or all three channels. If one sensor is on a
different channel than the advertising slave, it could potentially
“miss” the synchronization event. Further optimization would work to
ensure that all sensors scan the same channels together.

Conclusion
==========

The work I completed developing BlueSync has proven the ability to
create a reasonably performant time synchronization protocol using
Bluetooth Low Energy. Further, since the BlueSync protocol operates
above the MAC layer, it is possible to have heterogeneous networks,
where a broad range of devices and hardware implementing the BlueSync
service can synchronize on a single hub. Because of its low cost, low
power consumption, and pervasiveness in consumer devices, BLE is poised
to become very important in IoT applications going forward. However, in
order to realize its true potential, IoT applications will need to
develop open standards that will allow for a diverse ecosystem of
services and products.
