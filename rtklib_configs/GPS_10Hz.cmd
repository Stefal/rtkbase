# navigation data update rate 10Hz in ms
!UBX CFG-RATE 100 1 1

# turn on UBX RXM-RAWX messages on first(UART) interface with the same freq
!UBX CFG-MSG 2 21 0 1 0 0 0 0
# turn on UBX RXM-SFRBX messages on first(UART) interface with the same freq
!UBX CFG-MSG 2 19 0 1 0 0 0 0
# turn on UBX TIM TM2 messages on first(UART) interface with the same freq
!UBX CFG-MSG 13 3 0 1 0 0 0 0

# GNSS system settings
# set GPS 8-16 channels
!UBX CFG-GNSS 0 32 32 1 0 8 16 0 1 0 1 1

# set SBAS 1-3 channels
!UBX CFG-GNSS 0 32 32 1 1 1 3 0 1 0 1 1

# set Galileo 0 channels off
!UBX CFG-GNSS 0 32 32 1 2 0 0 0 0 0 0 1

# set BeiDou 8-16 channels off
!UBX CFG-GNSS 0 32 32 1 3 8 16 0 0 0 1 1

# set IMES 0-8 channels off
!UBX CFG-GNSS 0 32 32 1 4 0 8 0 0 0 1 1

# set QZSS 0-3 channels
!UBX CFG-GNSS 0 32 32 1 5 0 3 0 1 0 1 1

# set GLONASS 8-14 channels off
!UBX CFG-GNSS 0 32 32 1 6 8 14 0 0 0 1 1

# change NAV5 stationary mode to airborne <4g
!UBX CFG-NAV5 1 8 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0

# turn off extra messages default messages
# NMEA GGA
!UBX CFG-MSG 240 0 0 0 0 0 0 0
# NMEA GLL
!UBX CFG-MSG 240 1 0 0 0 0 0 0
# NMEA GSA
!UBX CFG-MSG 240 2 0 0 0 0 0 0
# NMEA GSV
!UBX CFG-MSG 240 3 0 0 0 0 0 0
# NMEA RMC
!UBX CFG-MSG 240 4 0 0 0 0 0 0
# NMEA VTG
!UBX CFG-MSG 240 5 0 0 0 0 0 0
# NMEA ZDA
!UBX CFG-MSG 240 8 0 0 0 0 0 0
!UBX CFG-MSG 1 3 0 0 0 0 0 0
!UBX CFG-MSG 1 3 0 0 0 0 0 0
!UBX CFG-MSG 1 6 0 0 0 0 0 0
!UBX CFG-MSG 1 18 0 0 0 0 0 0
!UBX CFG-MSG 1 34 0 0 0 0 0 0
!UBX CFG-MSG 1 48 0 0 0 0 0 0
@
!UBX CFG-RATE 1000 1 1
