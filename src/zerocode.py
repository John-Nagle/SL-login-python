# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/510399
# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/510399
def ByteToHex( byteStr ):
    """
    Convert a byte string to it's hex string representation e.g. for output.
    """
 
    # Uses list comprehension which is a fractionally faster implementation than
    # the alternative, more readable, implementation below
    #   
    #    hex = []
    #    for aChar in byteStr:
    #        hex.append( "%02X " % ord( aChar ) )
    #
    #    return ''.join( hex ).strip()        
 
    return ''.join( [ "%02X " % x for x in byteStr ] ).strip()
 
 
def HexToByte( hexStr ):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    # The list comprehension implementation is fractionally slower in this case    
    #
    #    hexStr = ''.join( hexStr.split(" ") )
    #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
    #                                   for i in range(0, len( hexStr ), 2) ] )
 
    bytes = []
 
    hexStr = ''.join( hexStr.split(" ") )
 
    for i in range(0, len(hexStr), 2):
        bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )
 
    return ''.join( bytes )
 
 
def zero_encode(inputbuf):
    newstring = b""
    zero = False
    zero_count = 0            
    for c in inputbuf:
        if c != '\0':
            if zero_count != 0:
                newstring = newstring + chr(zero_count)
                zero_count = 0
                zero = False
 
            newstring = newstring + c.to_bytes(1,'big')

        else:
            if zero == False:
                newstring = newstring + c.to_bytes(1,'big')
                zero = True
 
            zero_count = zero_count + 1
    if zero_count != 0:
        newstring = newstring + zero_count.to_bytes(1,'big')
 
 
    return newstring
 
def zero_decode(inputbuf):
    newstring =""
    in_zero = False
    for c in inputbuf:
        if c != '\0':
            if in_zero == True:
                zero_count = ord(c)
                zero_count = zero_count -1
                while zero_count>0:
 
                    newstring = newstring + '\0'
                    zero_count = zero_count -1
                in_zero = False
            else:
                newstring = newstring + c.to_bytes(1,'big')
        else:
            newstring = newstring + c.to_bytes(1,'big')
            in_zero = True
    return newstring
 
def zero_decode_ID(inputbuf):
    newstring =b''
    in_zero = False
    #print "in encode, input is", ByteToHex(inputbuf)
    for c in inputbuf:
        if c != '\0':
            if in_zero == True:
                zero_count = ord(c)
                zero_count = zero_count -1
                while zero_count>0:
 
                    newstring = newstring + '\0'
                    zero_count = zero_count -1
                in_zero = False
            else:
                newstring = newstring + c.to_bytes(1,'big')
        else:
            newstring = newstring + c.to_bytes(1,'big')
            in_zero = True
    return newstring[:4]
