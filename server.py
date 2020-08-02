from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
import socket
import threading
from urllib import request, error
import queue
from concurrent.futures import ThreadPoolExecutor

class LinksFinder:
    def __init__(self):
        self._my_regex = '(?<=<a href=")[^"]*'
        self.pattern = re.compile(self._my_regex)

    def get_links_from_current_link(self, link):
        html_file = request.urlopen(link, timeout=2.0)
        html_text = str(html_file.read())
        str_links = set(re.findall(self.pattern, html_text))
        return str_links


class WikiWebCrawler:
    def __init__(self, start_url, target_url):
        self.start_url = start_url
        self.target_url = target_url
        self._bfs_queue = queue.Queue()
        self._visited_depth = {}
        self._links_finder = LinksFinder()

    def find_path(self):
        self._bfs_queue.put(self.start_url)
        self._visited_depth[self.start_url] = 0
        with ThreadPoolExecutor(max_workers=50) as executer:
            links = []

            while not self._bfs_queue.empty():
                # early exit in case we found url_b
                if self.target_url in self._visited_depth.keys():
                    executer.shutdown(wait=False)
                    return True
                current_link = self._bfs_queue.get()

                # project's requirements
                if self._visited_depth[current_link] < 2:
                    links.append(current_link)

                # we want to wait before continue in case of:
                # the bfs queue is empty - since the running the threads might push new links to the queue
                if self._bfs_queue.empty():
                    results = executer.map(self.find_links_and_add_to_visited, links)
                    for _ in results:
                        pass
                    links = []
            if self.target_url in self._visited_depth.keys():
                return True

            print(len(self._visited_depth.keys()))

            return False

    def find_links_and_add_to_visited(self, link):
        links = self.get_wiki_links(link)
        for neighbour in links:
            if neighbour not in self._visited_depth.keys():
                self._visited_depth[neighbour] = self._visited_depth[link] + 1
                self._bfs_queue.put(neighbour)

    def get_wiki_links(self, link):
        wiki1 = 'http[s]?://([a-zA-Z.0-9]{,3}wikipedia.org/wiki/[/!@i^*$a-zA-Z0-9_-]*)(?:&quot)?'
        wiki2 = 'http[s]?://([a-zA-Z.0-9]{,3}wikipedia.org/wiki/[/!@i^*$a-zA-Z0-9_-]*\([/!@i^*$a-zA-Z0-9_-]*\)[/!@i^*$a-zA-Z0-9_-]*)(?:&quot)?'
        wiki = wiki1 + '|' + wiki2
        wiki_pat = re.compile(wiki)

        str_links = self._links_finder.get_links_from_current_link(link)

        try:
            wiki_links = []
            for link in str_links:
                if link.startswith("//"):  # missing scheme link
                    link = "https:" + link
                if not link.startswith('http'):  # relative link
                    link = 'https://en.wikipedia.org' + link
                if wiki_pat.match(link):
                    result = link.index('/wiki/')
                    if ":" in link[result + 6:]:
                        continue
                    else:
                        wiki_links.append(link)
            return list(set(wiki_links))  # removing duplicates and return
        # exceptions while making http request
        # in case of exception - print the error and return an empty link
        except socket.timeout:
            print("timeout for link - " + link)
        except error.HTTPError:
            print("Error for link - " + link)
        except Exception as e:
            print("Unknown Error for link: " + str(e))
        return []


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

        url_a = params_dict['url_a'][0]
        url_b = params_dict['url_b'][0]

        wiki_web_crawler = WikiWebCrawler(url_a, url_b)
        answer = wiki_web_crawler.find_path()
        self.wfile.write(str(answer).encode())


def main():
    PORT = 8000
    server = HTTPServer(('', PORT), HttpHandler)
    print('server running on port %s' % PORT)
    server.serve_forever()


if __name__ == '__main__':
    main()
