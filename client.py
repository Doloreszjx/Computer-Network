import socket
import sys
import random
import struct


def create_query(qid, qname, qtype):
    qname_encoded = qname.encode()
    qtype_encoded = qtype.encode()
    return struct.pack("!H", qid) + qname_encoded + b' ' + qtype_encoded


def main():
    if len(sys.argv) != 5:
        print("Usage: python3 client.py server_port qname qtype timeout")
        return

    server_port = int(sys.argv[1])
    qname = sys.argv[2]
    qtype = sys.argv[3]
    timeout = int(sys.argv[4])

    if qtype not in ['A', 'NS', 'CNAME']:
        print("Invalid query type. Use 'A', 'NS', or 'CNAME'.")
        return

    qid = random.randint(0, 65535)
    query = create_query(qid, qname, qtype)
    # print(query)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)


if __name__ == '__main__':
    main()
