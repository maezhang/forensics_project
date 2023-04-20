import http.server
import socketserver
import subprocess

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        uploaded_file = self.rfile.read(content_length)
        print(self.headers)
        # Save the uploaded file to disk
        # with open('uploads/' + self.headers['Filename'], 'wb') as f:
        with open('uploads/' + 'file.dd', 'wb') as f:
            f.write(uploaded_file)

        # Run python script on file.dd
        subprocess.run(["python", "forensics_project.py"])

        # Send a response back to the client
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        f = open('./report.html', 'rb')
        self.wfile.write(f.read())
        self.wfile.write(b'File uploaded successfully.')

PORT = 8000

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print("Server started at http://localhost:{}/".format(PORT))
    httpd.serve_forever()
