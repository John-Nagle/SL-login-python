# uses the client's message_template.msg file to create a dictionary of name and other relevant packet info...
# make sure that message_template.msg has had all leading spaces removed and replaced with the correct number of  tabs --I was exceedingly lazy when I wrote this and assumed a consistent tabbing scheme in the template
 
import re

depth=0

def fixtabs(line) :
    global depth
    #   Indent based on bracket depth, not tabs
    s = line.strip()
    if s.startswith("//"):
        return("")    # comment
    s = "\t" * depth + s
    #   Update indent depth
    for ch in line :
        if ch == "{" : 
            depth = depth + 1
        if ch == "}" :
            depth = depth - 1 
            if depth < 0 :
                print("Unmatched } in template file")
                exit(1)
                       
    return s
 
 
def makepacketdict():
    dict = {}
    global depth
    depth = 0
    for line in open("message_template.msg"):
        line = fixtabs(line)
        results = re.match("^\t([^\t{}]+.+)",line)
        if results:
            aline = results.group(1)
            aline = aline.split()
            if aline[1] == "Fixed": 
                dict[(aline[1],int(aline[2][8:],16))] = (aline[0],aline[3], aline[4])
            else:
                dict[(aline[1],int(aline[2]))] = (aline[0],aline[3], aline[4])
    return dict
