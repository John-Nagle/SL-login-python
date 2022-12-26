from struct import *
from zerocode import  *
import hashlib
import xmlrpc.client
import sys 
 
import re
import http, urllib  
import ssl      
## from urlparse import urlparse    
import socket, sys, time
import uuid
from makepacketdict import makepacketdict
 
 
 
from datetime import datetime
 
 
mypacketdictionary = {}
outputstring = ''
ack_need_list = []
 
logoutputflag = False
 
if logoutputflag:
    temp = sys.stdout
    sys.stdout =open('alog.txt','w')
 
def login(first, last, passwd, mac):
  m = hashlib.md5()
  m.update(bytes(passwd, 'utf-8'))
  passwd_md5 = '$1$' + m.hexdigest()
  ####passwd_md5 = '$1$' + hashlib.md5.new(passwd).hexdigest()
  print("Password MD5: ", passwd_md5);
 
  uri = 'http://127.0.0.1'
  uri = 'https://login.agni.lindenlab.com/cgi-bin/login.cgi'
  uri = 'https://login.aditi.lindenlab.com/cgi-bin/login.cgi'
  s = xmlrpc.client.ServerProxy(uri)
 
  login_details = {
    'first': first,
    'last': last,
    'passwd': passwd_md5,
    'start': 'last',
    'major': '1',
    'minor': '18',
    'patch': '5',
    'build': '3',
    'platform': 'Win',
    'mac': mac,
    'options': [],
    'user-agent': 'sl.py 0.1',
    'id0': '',
    'agree_to_tos': '',
    'viewer_digest': '09d93740-8f37-c418-fbf2-2a78c7b0d1ea'
  }
  results = s.login_to_simulator(login_details)
  print("Login result: ",results)
 
  return results
 
 
 
 
def get_caps(results,cap_key, request_keys):
 
  _, netloc, path, _, _, _ = urllib.parse.urlparse(results[cap_key])
 
  params = "<llsd><array><string>"+ request_keys[0]+"</string></array></llsd>"
  headers = {"content-type": "application/xml"}
  print("Get cap request to '%s' for %s" % ( results[cap_key], request_keys))
  
  
  conn = http.client.HTTPSConnection(netloc, context=ssl._create_unverified_context())
  #### No good #### conn = httplib.HTTPConnection(netloc)
 
  conn.request("POST", path, params, headers)
  response = conn.getresponse()
 
 
  data = response.read()
  print("Get caps response: ", data)
  conn.close()
  return data
 
def ExtractCap(cap_result):
  trim_xml = re.compile(r"<key>([a-zA-Z_]+)</key><string>([a-zA-Z_:/0-9-.]+)</string>")
  new_key = trim_xml.search(cap_result).group(1)
  new_cap = trim_xml.search(cap_result).group(2)
  return new_key, new_cap
 
 
 
def scheduleacknowledgemessage(data):
    if not data[0]&0x40:
        print("OOOPS! Got asked to ack a message that shouldn't be acked")
 
        return
    else:
        ID = data[1:5]
        if (data[0]&0x40) & 0x80: ID = zero_decode_ID(ID) #impossible
        ack_need_list.append(unpack(">L",ID)[0])
        #ack_need_list.append(unpack(">L",data[1:5])[0])
 
 
    return
 
def packacks():
    acksequence = b''
    for msgnum in ack_need_list:
        acksequence += pack("<L", msgnum)
 
 
    return acksequence
 
#def sendacks():
 #   if len(ack_need_list)>0:
 
 
#===============================================================================
# {
#    UUIDNameRequest Low NotTrusted Unencoded
#    {
#        UUIDNameBlock    Variable
#        {    ID            LLUUID    }
#    }
# }
#===============================================================================
 
def sendUUIDNameRequest(sock, port, host, currentsequence,aUUID):
 
    packed_data = b''
    fix_ID = int("ffff0000",16)+ 235
    data_header = pack('>BLB', 0x00,currentsequence,0x00) 
 
 
    for x in aUUID:
        packed_data += uuid.UUID(x).bytes
 
    packed_data += pack("L",fix_ID) + pack(">B",len(aUUID)) + packed_data
 
    sock.sendto(packed_data, (host, port)) 
    return              
 
def sendRegionHandshakeReply(sock, port, host, currentsequence,agentUUID,sessionUUID):
    packed_data = b''
 
    low_ID = "ffff00%2x" % 149
    data_header = pack('>BLB', 0x00,currentsequence,0x00)
    packed_data += uuid.UUID(agentUUID).bytes+uuid.UUID(sessionUUID).bytes+ pack(">L",0x00)
    packed_data = data_header + pack(">L",int(low_ID,16))+packed_data
    sock.sendto(packed_data, (host, port)) 
    print("Sending RegionHandshakeReply to server", ByteToHex(packed_data))
    return
 
 
 
def sendAgentUpdate(sock, port, host, currentsequence, result):
 
#AgentUpdate
 
    tempacks = packacks()
    del ack_need_list[:]
    if tempacks == "": 
        flags = 0x00
    else:
        flags = 0x10
 
    #print("tempacks is:", ByteToHex(tempacks))
    
    far_view_distance = 400.0 # View distance
 
    data_header = pack('>BLB', flags,currentsequence,0x00)
    packed_data_message_ID = pack('>B',0x04)
    packed_data_ID = uuid.UUID(result["agent_id"]).bytes + uuid.UUID(result["session_id"]).bytes
    packed_data_QuatRots = pack('<ffff', 0.0,0.0,0.0,1.0)+pack('<ffff', 0.0,0.0,0.0,1.0)  
    packed_data_State = pack('<B', 0x00)
    ####packed_data_Camera = pack('<fff', 0.0,0.0,0.0)+pack('<fff', 0.0,0.0,0.0)+pack('<fff', 0.0,0.0,0.0)+pack('<fff', 0.0,0.0,0.0)
    #   Camera: center, look at vector, left vector, up vector.
    packed_data_Camera = pack('<fff', 0.0,0.0,0.0)+pack('<fff', 1.0,1.0,0.0)+pack('<fff', 0.0,1.0,0.0)+pack('<fff', 0.0,0.0,1.0)
    packed_data_Flags = pack('<fLB', far_view_distance,0x00,0x00)
 
    encoded_packed_data = zero_encode(packed_data_message_ID+packed_data_ID+packed_data_QuatRots+packed_data_State+packed_data_Camera+packed_data_Flags)
 
    packed_data = data_header + encoded_packed_data+tempacks
 
    print("Sending Agent Update to server, seq #", currentsequence)
    # print("sending AgentUpdate to server",ByteToHex(data_header+zero_decode(encoded_packed_data)+ tempacks))
 
    sock.sendto(packed_data, (host, port))
    return
 
def sendCompletePingCheck(sock, port, host, currentsequence,data,lastPingSent):
#    print("data from PingCHeck", ByteToHex(data))
 
    data_header = pack('>BLB', 0x00,currentsequence,0x00)
    packed_data_message_ID = pack('>B',0x02)
    packed_data = data_header + packed_data_message_ID+pack('>B', lastPingSent)
    print("CompletePingCheck packet sent:", ByteToHex(packed_data))
    sock.sendto(packed_data, (host, port))
 
    return
 
def sendPacketAck(sock, port, host,currentsequence):
 
    tempacks = packacks()
    templen = len(ack_need_list)
    del ack_need_list[:]
    data_header = pack('>BLB',0x00,currentsequence,0x00) 
    packed_data_message_ID = pack('>L',0xFFFFFFFB)
    packed_ack_len = pack('>B',templen)
 
    packed_data = data_header + packed_data_message_ID + packed_ack_len + tempacks
#===============================================================================
#    t = datetime.now()
#    t.strftime("%H:%M:%S")
#    ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
#    print(ti, "PacketAck packet sent:", ByteToHex(packed_data))
#===============================================================================
    sock.sendto(packed_data, (host, port))
    return
 
def sendLogoutRequest(sock, port, host,seqnum,aUUID,sUUID):
    packed_data = ""
    packed_data_message_ID = pack('>L',0xffff00fc)
    data_header = pack('>BLB', 0x00,seqnum,0x00)
    packed_data += uuid.UUID(aUUID).bytes+uuid.UUID(sUUID).bytes+ pack(">L",0x00)
 
    packed_data = data_header + packed_data_message_ID + packed_data
    sock.sendto(packed_data, (host, port))
    return
 
 
def establishpresence(host, port, circuit_code):
 
 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#Sending packet UseCircuitCode <-- Inits the connection to the sim.
    data = pack('>BLBL',0x00,0x01,00,0xffff0003) + pack('<L',circuit_code) + uuid.UUID(result["session_id"]).bytes+uuid.UUID(result["agent_id"]).bytes
    sock.sendto(data, (host, port))
    print("Sent UseCircuitCode")
 
#ISending packet CompleteAgentMovement <-- establishes the agent's presence
    data = pack('>BLBL',0x00,0x02,00,0xffff00f9) + uuid.UUID(result["agent_id"]).bytes + uuid.UUID(result["session_id"]).bytes + pack('<L', circuit_code)
    sock.sendto(data, (host, port))
    print("Sent CompleteAgentMovement")
    sendAgentUpdate(sock, port, host, 3, result)
    print("Sent first AgentUpdate")
    aUUID = [result["agent_id"]]
    sendUUIDNameRequest(sock, port, host, 4,aUUID)
    print("Sent UUID name request")
#
 
    buf = 100
    i = 0
    trusted_count = 0
    ackable = 0
    trusted_and_ackable = 0
    ack_need_list_changed = False
    seqnum = 5
    lastPingSent = 0 
    trusted = 0
    while True:
        if ack_need_list_changed:
            ack_need_list_changed = False
            seqnum += 1
            sendPacketAck(sock, port, host,seqnum)
            #   Really should send an agent update once a second or so.
            #sendAgentUpdate(sock, port, host, seqnum, result)
            seqnum += 1
        #sendacks()
        i += 1
        data,addr = sock.recvfrom(buf)
        t = datetime.now()
        t.strftime("%H:%M:%S")
 
 
 
        if not data:
            print("Client has exited!")
 
            break
        else:
            test =  ByteToHex(data).split()
            #print(test)
            ID = data[6:12]
            #print("ID =", ByteToHex(ID))
            if data[0]&0x80:                 
                ID = zero_decode_ID(data[6:12])
                # print("Zero decode msg number: ",data[6:12], " -> ", ID)
 
            if data[0]&0x40: 
                scheduleacknowledgemessage(data); 
                ack_need_list_changed = True
            #print("ID =", ByteToHex(ID))
            #print("ID =", unpack(">L", ID[:4]))
            if ID[0] == ord(b'\xFF'):
                if ID[1] == ord(b'\xFF'):
                    if ID[2] == ord(b'\xFF'):
                        myentry = mypacketdictionary[("Fixed" , "0x"+ByteToHex(ID[0:4]).replace(' ', ''))]
                        if myentry[1] == "Trusted":
                            trusted += 1;
                        ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                        print(ti, "Message #", i, "trusted count is", trusted,"Flags: 0x" + test[0], myentry,  "sequence #", unpack(">L",data[1:5]))
 
                        #if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                        #if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print "trusted_and_ackable =", trusted_and_ackable
                        #if ord(data[0])&0x40: ackable += 1; print "number of ackable messages = ", ackable
                    else:
                        myentry = mypacketdictionary[("Low",int(ByteToHex(ID[2:4]).replace(' ', ''),16))]
                        if myentry[1] == "Trusted":
                            trusted += 1;
                        ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                        print(ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,   "sequence #", unpack(">L",data[1:5]))
                        if myentry[0] == "UUIDNameReply":
                            pass
                            #print(ByteToHex(data))
                            #print(data[:28])
                            #print(data[28:36],data[38:45])
                        elif myentry[0] == "RegionHandshake":
                            sendRegionHandshakeReply(sock, port, host, seqnum,result["agent_id"],result["session_id"])
                            seqnum += 1
 
                        #if myentry[1] == "Trusted": trusted_count += 1;print("number of trusted messages =", trusted_count)
                        #if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print("trusted_and_ackable =", trusted_and_ackable)
                        #if ord(data[0])&0x40: ackable += 1; print("number of ackable messages = ", ackable)
                else:
                    myentry = mypacketdictionary[("Medium", int(ByteToHex(ID[1:2]).replace(' ', ''),16))]
                    if myentry[1] == "Trusted":
                        trusted += 1;
                    ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                    print(ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,  "sequence #", unpack(">L",data[1:5]))
 
 
                    #if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                    #if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print("trusted_and_ackable =", trusted_and_ackable)
                    #if ord(data[0])&0x40: ackable += 1; print("number of ackable messages = ", ackable)
            else:
                # 1-byte message type
                ####myentry = mypacketdictionary[("High", int(ByteToHex(ID[0]), 16))]
                myentry = mypacketdictionary[("High", ID[0])] # one byte, no unpack needed
                if myentry[0] == "StartPingCheck": 
                    print("data from StartPingCheck", test)
                    sendCompletePingCheck(sock, port, host, seqnum,data,lastPingSent)
                    lastPingSent += 1
                    seqnum += 1
 
                if myentry[1] == "Trusted":
                    trusted += 1;   
                ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
 
                print(ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,   "sequence #", unpack(">L",data[1:5]))
 
                #if myentry[1] == "Trusted": trusted_count += 1;print("number of trusted messages =", trusted_count)
                #if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print("trusted_and_ackable =",  trusted_and_ackable)
                #if ord(data[0])&0x40: ackable += 1; print("number of ackable messages = ", ackable)
 
    sendLogoutRequest(sock, port, host,seqnum,myAgentID,mySessionID)
 
    sock.close()
    print("final number of trusted messages =", trusted_count)
 
    return
 
 
#   Main program
#   Login credentials 
MAC="60:a4:4c:cf:3f:5a" # dummy

mypacketdictionary = makepacketdict()   # message formats, from the message template file.
#   Prompt for user name and password
print("Second Life login, main grid.")
loginname = input("User name: ")
firstlast = re.split(r'[\W\.]+', loginname.strip()) # split on whitespace or periods.
if len(firstlast) == 1 :
    firstlast.append("Resident")
elif len(firstlast) != 2 :
    print("User name must be FIRSTNAME LASTNAME or FIRSTNAME")
    exit()
    
password = input("Password for %s %s: " % (firstlast[0], firstlast[1]))
print("Starting login.")
result = login(firstlast[0], firstlast[1], password, MAC)
 
myhost = result["sim_ip"]
myport = result["sim_port"]
mycircuit_code = result["circuit_code"]

notes_cap = get_caps(result,"seed_capability", ["ServerReleaseNotes"])
mesh_cap = get_caps(result,"seed_capability", ["GetMesh"])
render_materials_cap = get_caps(result,"seed_capability", ["RenderMaterials"])
print("Notes cap: %s" % (notes_cap))
print("Mesh cap: %s" % (mesh_cap))
print("Render materials cap: %s" % (render_materials_cap))

establishpresence(myhost, myport, mycircuit_code)
 

