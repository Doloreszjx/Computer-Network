import socket
import sys
import random
import json
import time


def create_query(qid, qname, qtype):
    timestamp = int(round(time.time()*1000))
    query_data = {
        'qid': qid,
        'qname': qname,
        'qtype': qtype,
        'qtime': timestamp
    }
    # print(f"Sending query to server: {query_data}")
    return json.dumps(query_data).encode()


def dic_to_str(ori_dic):
    kv_pairs = [f'{key}: {value}' for key, value in ori_dic.items()]
    result = ', '.join(kv_pairs)
    return result


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

    client_socket.sendto(query, ("127.0.0.1", server_port))

    try:
        response, _ = client_socket.recvfrom(1024)
        response_data = json.loads(response.decode())
        # print("Response from server:", response_data)

        qid = response_data.get('qid')
        qname = response_data.get('qname')
        qtype = response_data.get('qtype')
        answer_section = response_data.get('answer')
        authority_section = response_data.get('authority')
        additional_section = response_data.get('additional')
        answers = []
        authorities = []
        additionals = []
        for ele in answer_section:
            format_ele = dic_to_str(ele)
            answers.append(format_ele)

        for au_ele in authority_section:
            format_ele = dic_to_str(au_ele)
            authorities.append(format_ele)

        for ad_ele in additional_section:
            format_ele = dic_to_str(ad_ele)
            additionals.append(format_ele)
        # print('response_data:', qid, qname, qtype, answers)
        if qtype in ['A', 'NS', 'CNAME']:
            print('ID: ', qid)
            print('\n')
            print('QUESTION SECTION:\n', qname, qtype)
            if len(answers):
                print('\n')
                print('ANSWER SECTION:')
                for item in answers:
                    print(item)
            if len(authorities):
                print('\n')
                print('AUTHORITY SECTION:')
                for item in authorities:
                    print(item)
            if len(additionals):
                print('\n')
                print('ADDITIONAL SECTION:')
                for item in additionals:
                    print(item)
        else:
            print(f"Unknown type {qtype}: qname: {qname}")

    except socket.timeout:
        print("Request timed out")
    finally:
        client_socket.close()


if __name__ == '__main__':
    main()
