from configparser import RawConfigParser

#faking a default section

parser = RawConfigParser()
with open("../rtkbase/settings.conf") as stream:
    parser.read_string("[top]\n" + stream.read().strip('\t'))  # This line does the trick.

# list keys values
for key in parser['top']:
    print("{} : {} ".format(key, parser['top'].get(key)))

