import socket
import sys
import random
import json


def create_query(qid, qname, qtype):
    query_data = {
        'id': qid,
        'name': qname,
        'type': qtype
    }
    print(f"Sending query to server: {query_data}")
    return json.dumps(query_data).encode()


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

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)

    qid = random.randint(0, 65535)
    query = create_query(qid, qname, qtype)
    print(query)
    client_socket.sendto(query, ("127.0.0.1", server_port))

    try:
        response, _ = client_socket.recvfrom(1024)
        response_data = json.loads(response.decode())
        print("Response from server:", response_data)

        qid, qname, qtype, data = response_data

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
