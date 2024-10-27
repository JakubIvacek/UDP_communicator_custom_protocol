-- Define the new protocol
local my_protocol = Proto("myprotocol", "My Custom Protocol")

-- Define the fields for the protocol
local f_header_type = ProtoField.uint8("myprotocol.header_type", "Header Type", base.DEC)
local f_sequence_number = ProtoField.uint16("myprotocol.sequence_number", "Sequence Number", base.DEC)
local f_acknowledgment_number = ProtoField.uint16("myprotocol.acknowledgment_number", "Acknowledgment Number", base.DEC)
local f_window_size = ProtoField.uint16("myprotocol.window_size", "Window Size", base.DEC)
local f_data_length = ProtoField.uint16("myprotocol.data_length", "Data Length", base.DEC)
local f_crc = ProtoField.uint16("myprotocol.crc", "CRC", base.HEX)
local f_flags = ProtoField.string("myprotocol.flags", "Flags")
local f_payload = ProtoField.bytes("myprotocol.payload", "Payload Data")

my_protocol.fields = {f_header_type, f_sequence_number, f_acknowledgment_number, f_window_size, f_data_length, f_crc, f_flags, f_payload}

-- Create a dissector function
function my_protocol.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = my_protocol.name

    -- Check if buffer length is sufficient for header
    if buffer:len() < 11 then
        return
    end

    local subtree = tree:add(my_protocol, buffer(), "My Protocol Data")
    local flag = ""
    local header_type = buffer(0, 1):uint()

    -- Determine flags based on header_type
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

    -- Add fields to the subtree
    subtree:add(f_header_type, header_type)
    subtree:add(f_flags, flag)
    subtree:add(f_sequence_number, buffer(1, 2))
    subtree:add(f_acknowledgment_number, buffer(3, 2))
    subtree:add(f_window_size, buffer(5, 2))
    subtree:add(f_data_length, buffer(7, 2))
    subtree:add(f_crc, buffer(9, 2))

    -- Extract and add payload data
    local payload_offset = 11
    local data_length = buffer(7, 2):uint()

    if buffer:len() >= payload_offset + data_length then
        local payload = buffer(payload_offset, data_length)
        subtree:add(f_payload, payload)  -- Add the payload to the subtree
    else
        subtree:add(f_payload, buffer(payload_offset, buffer:len() - payload_offset))  -- Add remaining buffer as payload
    end
end

-- Register the protocol to a specific port (replace 1234 with your port)
local udp_table = DissectorTable.get("udp.port")
udp_table:add(1234, my_protocol)

