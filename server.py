import socket
import sys
import threading
import json
import time


def time_to_date(timestamp):
    datettime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000))
    return datettime


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


# def recursive_query(domain, qtype, records, visited=None):
#     if visited is None:
#         visited = []

#     if qtype == 'A':
#         if domain in records and 'A' in records[domain]:
#             print('domain, qtype, records:', domain, qtype, records)
#             return domain, 'A', records[domain]['A']
#     elif qtype == 'NS':
#         if domain in records and 'NS' in records[domain]:
#             ns_domain = records[domain]['NS']
#             return recursive_query(ns_domain, 'A', records, visited)
#     elif qtype == 'CNAME' or (domain in records and 'CNAME' in records[domain]):
#         cname_domain = records[domain]['CNAME']
#         if cname_domain not in visited:
#             visited.append(cname_domain)
#             return recursive_query(cname_domain, 'A', records, visited)
#     return None, None, None

def recursive_query(domain, qtype, records, visited=None):
    if visited is None:
        visited = []

    if qtype == 'A':
        if domain in records and 'A' in records[domain]:
            # print('domain, qtype, records:', domain, qtype, records)
            return domain, 'A', records[domain]['A']
    elif qtype == 'NS':
        if domain in records and 'NS' in records[domain]:
            ns_domain = records[domain]['NS']
            return recursive_query(ns_domain, 'A', records, visited)
    elif qtype == 'CNAME' or (domain in records and 'CNAME' in records[domain]):
        cname_domain = records[domain]['CNAME']
        if cname_domain not in visited:
            print('NS:', domain, cname_domain)
            visited.append(cname_domain)
            return recursive_query(cname_domain, 'A', records, visited)
    return None, None, None


def handle_client(query, server_port, server_socket, client_address, records):
    query_data = json.loads(query.decode())
    qid = query_data['qid']
    qname = query_data['qname']
    qtype = query_data['qtype']
    recv_time = query_data['qtime']
    recv_date = time_to_date(int(recv_time))

    response_data = {
        'qid': qid,
        'qname': qname,
        'qtype': qtype,
        'ANSWER_SECTION': [],
        # 'AUTHORITY SECTION': [],
        # 'ADDITIONAL SECTION': []
    }

    visited = []

    while True:
        data_domain, data_type, data = recursive_query(
            qname, qtype, records, visited)
        if data:
            response_data['ANSWER_SECTION'].append(
                {'domain': data_domain, 'type': data_type, 'data': data})
            if data_type == 'CNAME' and qtype != 'CNAME':
                qname = data
                qtype = 'A'
            else:
                break
        else:
            response_data['ANSWER_SECTION'].append(
                {'domain': qname, 'type': qtype, 'data': 'No such record'})
            break

    response = json.dumps(response_data).encode()
    send_time = int(round(time.time()*1000))
    date_send_time = time_to_date(send_time)
    delay_time = (send_time - recv_time) / 1000

    if delay_time != 0:
        print(
            f"{recv_date} rcv {server_port}: {qid} {qname} {qtype} (delay: {delay_time}s)")
    else:
        print(f"{recv_date} rcv {server_port}: {qid} {qname} {qtype}")

    print(f"{date_send_time} snd {server_port}: {qid} {qname} {qtype}")

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
            args=(query, server_port, server_socket, client_address, records)
        )
        client_handler.start()


if __name__ == "__main__":
    main()
