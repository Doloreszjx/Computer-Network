import socket
import sys
import threading
import json


def load_master_file(filename):
    records = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split()
            domain, rtype, data = parts[0], parts[1], parts[2]
            if domain not in records:
                records[domain] = {}
            records[domain][rtype] = data
    return records


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


def handle_client(server_socket, client_address, records):
    print('handle_client1')
    query, _ = server_socket.recvfrom(1024)
    query_data = json.loads(query.decode())
    qid = query_data['id']
    qname = query_data['name']
    qtype = query_data['type']
    print('handle_client2')

    print(f"Received query: qname={qname}, qtype={qtype}")

    response_data = {'id': qid, 'name': qname, 'type': qtype, 'data': []}

    visited = []

    while True:
        data_domain, data_type, data = recursive_query(
            qname, qtype, records, visited)
        if data:
            response_data['data'].append(
                {'domain': data_domain, 'type': data_type, 'data': data})
            if data_type == 'CNAME' and qtype != 'CNAME':
                qname = data
                qtype = 'A'
            else:
                break
        else:
            response_data['data'].append(
                {'domain': qname, 'type': qtype, 'data': 'No such record'})
            break

    response = json.dumps(response_data).encode()
    print(f"Sending response: {response}")
    server_socket.sendto(response, client_address)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 server.py server_port")
        return

    server_port = int(sys.argv[1])
    records = load_master_file("sample_master.txt")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("127.0.0.1", server_port))

    print(f"Server listening on port {server_port}")

    while True:
        query, client_address = server_socket.recvfrom(1024)
        client_handler = threading.Thread(
            target=handle_client,
            args=(server_socket, client_address, records)
        )
        client_handler.start()


if __name__ == "__main__":
    main()
