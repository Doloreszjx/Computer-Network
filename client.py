import socket
import sys
import random
import struct


def create_query(qid, qname, qtype):
    # print('create_query')
    qname_encoded = qname.encode()
    qtype_encoded = qtype.encode()
    return struct.pack("!H", qid) + qname_encoded + b' ' + qtype_encoded
    # message = f'{qid},{qname},{qtype}'
    # return message.encode()


def parse_response(response):
    print('parse_response')
    qid, rest = struct.unpack("!H", response[:2]), response[2:].decode()
    qname, qtype, data = rest.split(' ', 2)
    return qid, qname, qtype, data


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

    try:
        client_socket.sendto(query, ("127.0.0.1", server_port))
        response, _ = client_socket.recvfrom(1024)
        print("Response from server:", response[2:].decode())

        qid, qname, qtype, data = parse_response(response)

        if qtype == 'A':
            print(f"Address: {data}")
        elif qtype == 'NS':
            print(f"Name Server: {data}")
        elif qtype == 'CNAME':
            print(f"Canonical Name: {data}")
        else:
            print(f"Unknown type {qtype}: {data}")

    except socket.timeout:
        print("Request timed out")
    finally:
        client_socket.close()


if __name__ == '__main__':
    main()
