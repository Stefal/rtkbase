from os import system

def sh(script):
    system("bash -c '%s'" % script)

# change baudrate to 230400
def br230400():
    cmd = ["echo", "-en", '"\\xb5\\x62\\x06\\x00\\x01\\x00\\x01\\x08\\x22\\xb5\\x62\\x06\\x00\\x14\\x00\\x01\\x00\\x00\\x00\\xd0\\x08\\x00\\x00\\x00\\x84\\x03\\x00\\x07\\x00\\x03\\x00\\x00\\x00\\x00\\x00\\x84\\xe8\\xb5\\x62\\x06\\x00\\x01\\x00\\x01\\x08\\x22"', ">", "/dev/ttyMFD1"]
    cmd = " ".join(cmd)
    sh(cmd)

# change baudrate to 230400 from any previous baudrates
def changeBaudrateTo230400():
    # typical baudrate values
    br = ["4800", "9600", "19200", "38400", "57600", "115200", "230400"]
    cmd = ["stty", "-F", "/dev/ttyMFD1"]

    for rate in br:
        cmd.append(str(rate))
        cmd_line = " ".join(cmd)
        sh(cmd_line)

        br230400()
        cmd.pop()
