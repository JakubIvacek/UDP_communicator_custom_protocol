-- Define the new protocol
local my_protocol = Proto("myprotocol", "My Custom Protocol")

-- Define the fields for the protocol
local f_header_type = ProtoField.uint8("myprotocol.header_type", "Header Type", base.DEC)
local f_packet_number = ProtoField.uint16("myprotocol.packet_number", "Packet Number", base.DEC)
local f_data_length = ProtoField.uint16("myprotocol.data_length", "Data Length", base.DEC)
local f_crc = ProtoField.uint16("myprotocol.crc", "CRC", base.HEX)
local f_flags = ProtoField.string("myprotocol.flags", "Flags")
local f_payload = ProtoField.bytes("myprotocol.payload", "Payload Data")

my_protocol.fields = {f_header_type, f_packet_number, f_data_length, f_crc, f_flags, f_payload}

-- Create a dissector function
function my_protocol.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = my_protocol.name

    -- Check if buffer length is sufficient for the header (7 bytes minimum)
    if buffer:len() < 7 then
        return
    end

    -- Add protocol subtree
    local subtree = tree:add(my_protocol, buffer(), "My Protocol Data")

    -- Extract header fields
    local header_type = buffer(0, 1):uint()
    local packet_number = buffer(1, 2):uint()
    local data_length = buffer(3, 2):uint()
    local crc = buffer(5, 2):uint()

    -- Determine flag description based on header_type
    local flag = ""
    if header_type == 0 then
        flag = "SYN"
    elseif header_type == 1 then
        flag = "SYN-ACK"
    elseif header_type == 2 then
        flag = "ACK"
    elseif header_type == 3 then
        flag = "MESSAGE TRANSFER"
    elseif header_type == 4 then
        flag = "EXIT"
    elseif header_type == 5 then
        flag = "FILE TRANSFER"
    elseif header_type == 6 then
        flag = "DATA PACKET"
    elseif header_type == 7 then
        flag = "NACK"
    else
        flag = "Unknown"
    end

    -- Add header fields to the subtree
    subtree:add(f_header_type, buffer(0, 1)):append_text(" (" .. flag .. ")") -- Show flag alongside type
    subtree:add(f_packet_number, buffer(1, 2))
    subtree:add(f_data_length, buffer(3, 2))
    subtree:add(f_crc, buffer(5, 2))

    -- Extract and add payload data (if present)
    local payload_offset = 7
    if buffer:len() > payload_offset then
        local payload = buffer(payload_offset, math.min(data_length, buffer:len() - payload_offset))
        subtree:add(f_payload, payload)
    end
end

-- Register the protocol to a specific port (replace 1234 with your port)
local udp_table = DissectorTable.get("udp.port")
udp_table:add(1234, my_protocol)