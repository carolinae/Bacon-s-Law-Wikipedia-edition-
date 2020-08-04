import sys
import time
from urllib import request


def check_client_input(url):
    if not url.startswith('http://en.wikipedia.org') and not url.startswith('https://en.wikipedia.org'):
        return False
    return True


def main():
    start = time.time()
    if len(sys.argv) < 3:
        print("Missing arguments")
        return

    url_a = str(sys.argv[1])
    if not check_client_input(url_a):
        print("ERROR: URL_A is not a valid wikipedia link!")
        return

    url_b = str(sys.argv[2])
    if not check_client_input(url_b):
        print("ERROR: URL_B is not a valid wikipedia link!")
        return

    response = request.urlopen("http://localhost:8000?url_a="+str(url_a)+"&url_b="+str(url_b))
    response_body = response.read().decode("utf-8")

    print(response_body)
    end = time.time()
    print(end-start)


if __name__ == '__main__':
    main()