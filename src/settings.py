import logging

SRV_NAME = "network-monitor"
SRV_DISPLAY_NAME= "Network Monitor"
SRV_HANDLE_FREQ_SEC = 20
SRV_TIMER_DEQUE_SIZE = 5
LOG_FILE = "network-monitor.log"
LOG_LEVEL = logging.DEBUG

PING_PACKET_COUNT = 4
PING_TIMEOUT = 2
TCP_TIMEOUT = 2