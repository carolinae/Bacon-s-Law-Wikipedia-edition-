from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
import socket
import threading
from urllib import request, error
import queue

MAX_THREADS = 1000


def get_links_from_current_link(link):
    my_regex = '(?<=<a href=")[^"]*'
    pattern = re.compile(my_regex)

    wiki1 = 'http[s]?://([a-zA-Z.0-9]{,3}wikipedia.org/wiki/[/!@i^*$a-zA-Z0-9_-]*)(?:&quot)?'
    wiki2 = 'http[s]?://([a-zA-Z.0-9]{,3}wikipedia.org/wiki/[/!@i^*$a-zA-Z0-9_-]*\([/!@i^*$a-zA-Z0-9_-]*\)[/!@i^*$a-zA-Z0-9_-]*)(?:&quot)?'
    wiki = wiki1 + '|' + wiki2
    wiki_pat = re.compile(wiki)

    try:
        html_file = request.urlopen(link, timeout=2.0)
        html_text = str(html_file.read())
        str_links = set(re.findall(pattern, html_text))
        links = []
        for link in str_links:
            if link.startswith("//"):  # missing scheme link
                link = "https:"+link
            if not link.startswith('http'):  # relative link
                link = 'https://en.wikipedia.org' + link
            if wiki_pat.match(link):
                result = link.index('/wiki/')
                if ":" in link[result+6:]:
                    continue
                else:
                    links.append(link)
        return list(set(links))  # removing duplicates and return
    # exceptions while making http request
    # in case of exception - print the error and return an empty link
    except socket.timeout:
        print("timeout for link - "+link)
    except error.HTTPError:
        print("Error for link - "+link)
    except Exception as e:
        print("Unknown Error for link: "+str(e))
    return []


def bfs(visited_depth, bfs_queue, url_a, url_b):
    bfs_queue.put(url_a)
    visited_depth[url_a] = 0
    threads = []
    while not bfs_queue.empty():
        # early exit in case we found url_b
        if url_b in visited_depth.keys():
            # we want to terminate all of the threads that are still running
            for t in threads:
                t.join()
            return True
        print(len(visited_depth.keys()))
        current_link = bfs_queue.get()

        # project's requirements
        if visited_depth[current_link] < 6:
            t1 = threading.Thread(target=find_links_and_add_to_visited, args=(current_link, visited_depth, bfs_queue))
            t1.start()
            threads.append(t1)
        # we want to wait before continue in case of:
        # 1. we've reached the maximum amount of allowed threads
        # 2. the bfs queue is empty - since the running the threads might push new links to the queue
        if len(threads) >= MAX_THREADS or bfs_queue.empty():
            for t in threads:
                t.join()
            threads = []
    if url_b in visited_depth.keys():
        return True
    return False


def find_links_and_add_to_visited(s, visited_depth, queue2):
    links = get_links_from_current_link(s)
    for neighbour in links:
        if neighbour not in visited_depth.keys():
            visited_depth[neighbour] = visited_depth[s] + 1
            queue2.put(neighbour)


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params_dict = parse_qs(urlparse(self.path).query)
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        # we want to know whether the relevant param queries are in dict keys
        if 'url_a' not in params_dict.keys() or 'url_b' not in params_dict.keys():
            self.wfile.write(b"Error: missing parameter url_a or url_b!")
            return
        bfs_queue = queue.Queue()
        visited_depth = {}
        url_a = params_dict['url_a'][0]
        url_b = params_dict['url_b'][0]
        answer = bfs(visited_depth, bfs_queue, url_a, url_b)
        self.wfile.write(str(answer).encode())


def main():
    PORT = 8000
    server = HTTPServer(('', PORT), HttpHandler)
    print('server running on port %s' % PORT)
    server.serve_forever()


if __name__ == '__main__':
    main()