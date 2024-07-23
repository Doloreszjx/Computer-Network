import socket
import sys
import threading
import json
import time


def time_to_date(timestamp):
    datettime = time.strftime(
        '%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000))
    return datettime


def load_master_file(filename):
    records = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split()
            domain, rtype, data = parts[0], parts[1], parts[2]
            if domain not in records:
                records[domain] = {}
            if rtype not in records[domain]:
                records[domain][rtype] = []
            records[domain][rtype].append(data)
    return records


def recursive_query(domain, qtype, records, cname_visited=None):
    if cname_visited is None:
        cname_visited = []

    if domain in records:
        if qtype in records[domain]:
            return domain, qtype, records[domain][qtype]
        elif 'CNAME' in records[domain]:
            cname_domain = records[domain]['CNAME'][0]
            if cname_domain not in cname_visited:
                # cname_visited.append(cname_domain)
                cname_visited.append(f'{domain},{cname_domain}')
                return recursive_query(cname_domain, qtype, records, cname_visited)

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
        'answer': [],
        'authority': [],
        'additional': []
    }

    # Query resolution
    cname_visited = []
    data_domain, data_type, data = recursive_query(
        qname, qtype, records, cname_visited)

    print('cname_visited', cname_visited)
    print('data', data)

    # Handling response
    if len(cname_visited):
        for domain_cname in cname_visited:
            domain_cname_str = domain_cname.split(',')
            domain = domain_cname_str[0]
            cname = domain_cname_str[1]
            response_data['answer'].append({
                'domain': domain,
                'type': 'CNAME',
                'data': cname
            })
    if data:
        for item in data:
            response_data['answer'].append(
                {'domain': data_domain, 'type': data_type, 'data': item})
    else:
        print('No data')
        # If no answer is found, add authority section if possible
        closest_domain = qname
        root_domain = '.'

        print(
            'wwww', closest_domain in records and 'NS' in records[closest_domain])

        while closest_domain:
            if closest_domain in records and 'NS' in records[closest_domain]:
                for ns_record in records[closest_domain]['NS']:
                    response_data['authority'].append({
                        'domain': closest_domain,
                        'type': 'NS',
                        'data': ns_record
                    })
                    if ns_record in records and 'A' in records[ns_record]:
                        for a_record in records[ns_record]['A']:
                            response_data['additional'].append({
                                'domain': ns_record,
                                'type': 'A',
                                'data': a_record
                            })
                break
            if '.' in closest_domain:
                closest_domain = closest_domain.split('.', 1)[1]

            else:
                break
        print('closest_domain:',
              (closest_domain in records and 'NS' in records[closest_domain]))
        if root_domain in records and 'NS' in records[root_domain] and not (closest_domain in records and 'NS' in records[closest_domain]):
            for ns_record in records[root_domain]['NS']:
                response_data['authority'].append({
                    'domain': root_domain,
                    'type': 'NS',
                    'data': ns_record
                })
                if ns_record in records and 'A' in records[ns_record]:
                    for a_record in records[ns_record]['A']:
                        response_data['additional'].append({
                            'domain': ns_record,
                            'type': 'A',
                            'data': a_record
                        })
    response = json.dumps(response_data).encode()
    send_time = int(round(time.time() * 1000))
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
    records = load_master_file("master.txt")

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
