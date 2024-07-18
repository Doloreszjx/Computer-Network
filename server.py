import socket
import sys
import threading
import struct


# Read master file, load resource records
def load_master_file(filename):
    records = {}

    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 3:
                print('format error!\n Useage: domain type data')
                return
            domain, rtype, data = parts[0], parts[1], parts[2]
            if domain not in records:
                records[domain] = {}
            records[domain][rtype] = data
    # print('records: ', records)
    return records

# 递归查询函数


def recursive_query(domain, qtype, records, visited=None):
    if visited is None:
        visited = []

    if qtype == 'A':
        if domain in records and 'A' in records[domain]:
            return domain, 'A', records[domain]['A']
    elif qtype == 'NS':
        if domain in records and 'NS' in records[domain]:
            ns_domain = records[domain]['NS']
            return recursive_query(ns_domain, 'A', records, visited)
    elif qtype == 'CNAME' or (domain in records and 'CNAME' in records[domain]):
        cname_domain = records[domain]['CNAME']
        if cname_domain not in visited:
            visited.append(cname_domain)
            return recursive_query(cname_domain, 'A', records, visited)
    return None, None, None

# 处理客户端请求


def handle_client(server_socket, client_address, records):
    print('handle_client')
    query, _ = server_socket.recvfrom(1024)
    print(query)
    qid, rest = struct.unpack("!H", query[:2]), query[2:].decode()
    qname, qtype = rest.split()

    print(f"Received query: qname={qname}, qtype={qtype}")

    response = struct.pack("!H", qid[0]) + \
        qname.encode() + b' ' + qtype.encode()

    original_qname = qname
    original_qtype = qtype
    visited = []

    while True:
        data_domain, data_type, data = recursive_query(
            qname, qtype, records, visited)
        if data:
            response += b' ' + data.encode()
            if data_type == 'CNAME' and original_qtype != 'CNAME':
                qname = data
                qtype = original_qtype
                response = struct.pack("!H", qid[0]) + original_qname.encode(
                ) + b' ' + original_qtype.encode() + b' CNAME ' + data.encode()
            else:
                break
        else:
            response += b' No such record'
            break
    print('server response:', response)
    server_socket.sendto(response, client_address)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 server.py server_port")
        return

    server_port = int(sys.argv[1])
    records = load_master_file('sample_master.txt')
    print(records)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("127.0.0.1", server_port))

    print(f"Server listening on port {server_port}")

    while True:
        query, client_address = server_socket.recvfrom(1024)
        print('server:', query)
        client_handler = threading.Thread(
            target=handle_client,
            args=(server_socket, client_address, records)
        )
        client_handler.start()


if __name__ == '__main__':
    main()
