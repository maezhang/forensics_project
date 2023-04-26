import http.server
import socketserver
import subprocess
import re
import os
import urllib.request, urllib.parse, urllib.error
import html
import shutil
import mimetypes
from io import BytesIO
import json
from jinja2 import Environment, FileSystemLoader

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()
        print((r, info, "by: ", self.client_address))
        f = BytesIO()
        f.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        length = f.tell()
        f.seek(0)

        # find uploaded image file name
        search = 'uploads/'
        tmp_str = info[info.find(search)+len(search):]
        image_file = tmp_str[:tmp_str.find("'")]

        # trigger processing script
        subprocess.run(["python", "forensics_project.py", image_file])
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()

        if not r:
            self.wfile.write(b'Something went wrong.')
            return
        
        # render new html
        with open('report.json', 'r') as d:
            report = json.load(d)

        fileLoader = FileSystemLoader('templates')
        env = Environment(loader=fileLoader)
        rendered = env.get_template('report_template.html').render(report=report, title="Report")

        with open('report.html', 'w') as f:
            f.write(rendered)

        f = open('./report.html', 'rb')
        self.wfile.write(f.read())

        
    def deal_post_data(self):
        content_type = self.headers['content-type']
        if not content_type:
            return (False, "Content-Type header doesn't contain boundary")
        boundary = content_type.split("=")[1].encode()
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()
        remainbytes -= len(line)
        fn = re.findall(r'Content-Disposition.*name="file"; filename="(.*)"', line.decode())
        if not fn:
            return (False, "Can't find out file name...")
        path = self.translate_path(self.path)
        fn = os.path.join(path, fn[0])
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        print('my path', fn)
        try:
            out = open(fn, 'wb')
        except IOError:
            return (False, "Can't create file to write, do you have permission to write?")
                
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                preline = preline[0:-1]
                if preline.endswith(b'\r'):
                    preline = preline[0:-1]
                out.write(preline)
                out.close()
                return (True, "File '%s' upload success!" % fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpect Ends of data.")

PORT = 8000

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("Server started at http://localhost:{}/".format(PORT))
    httpd.serve_forever()
