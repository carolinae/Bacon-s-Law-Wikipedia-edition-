from urllib import request
import sys
import time


def main():
    start = time.time()
    if len(sys.argv)<3:
        print("Missing arguments")
        return
    url_a = str(sys.argv[1])
    url_b = str(sys.argv[2])
    response = request.urlopen("http://localhost:8000?url_a="+str(url_a)+"&url_b="+str(url_b))
    response_body = response.read().decode("utf-8")
    print(response_body)
    end = time.time()
    print(end-start)



if __name__ == '__main__':
    main()