from configparser import RawConfigParser

#faking a default section

parser = RawConfigParser()
with open("../rtkbase/settings.conf") as stream:
    parser.read_string("[top]\n" + stream.read().strip('\t'))  # This line does the trick.

# list keys values
for key in parser['top']:
    print("{} : {} ".format(key, parser['top'].get(key)))

#remove comment and tabulations
for key in parser['top']:
    value = parser['top'][key]
    value = value.rsplit('#')[0]
    #remove tab
    value = value.strip("\t")
    
    value = value.strip()
    print(value)
    parser['top'][key] = value
