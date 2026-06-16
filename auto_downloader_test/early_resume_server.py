# add the line "127.0.0.1 cynteract.com" to your C:\Windows\System32\drivers\etc\hosts file
# python early_resume_server.py
# caddy run
# 
# A succeeding curl command on Linux/WSL would be:
# curl --fail --retry 5 --retry-connrefused --continue-at - -o file "https://cynteract.com/downloads/Cynteract.exe"


import socket
import threading

# host on all interfaces so that WSL can connect
HOST = '127.0.0.1'
PORT = 8000
TOTAL = 1024 * 1024  # advertised total size (1 MiB)
FIRST_SEND = 300 * 1024  # send this much then close (300 KiB)
EXE_PATH = "/downloads/Cynteract.exe"
VERSIONS_PATH = "/downloads/versions.json"

DATA = b'A' * TOTAL
VERSIONS_JSON = (
    '{"latestVersion":"3.6.1","downloadUrl":"https://cynteract.com/downloads/Cynteract.exe"}\n'
).encode('ascii')

def parse_range(header):
    # header like "Range: bytes=12345-"
    try:
        _, val = header.split(":", 1)
        val = val.strip()
        if not val.startswith("bytes="): return None
        r = val[len("bytes="):].split("-", 1)[0]
        return int(r) if r else None
    except:
        return None

def handle_conn(conn, addr):
    try:
        req = b""
        while b"\r\n\r\n" not in req:
            chunk = conn.recv(4096)
            if not chunk:
                return
            req += chunk
        req_text = req.decode('iso-8859-1')
        first_line = req_text.splitlines()[0]
        path = first_line.split()[1]
        # find Range header if present
        range_header = None
        for line in req_text.splitlines():
            if line.lower().startswith("range:"):
                range_header = line
                break

        if path == VERSIONS_PATH:
            headers = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Length: {len(VERSIONS_JSON)}\r\n"
                "Content-Type: application/json\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            conn.sendall(headers.encode('ascii'))
            conn.sendall(VERSIONS_JSON)
            return

        if path != EXE_PATH:
            resp = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            conn.sendall(resp.encode('ascii'))
            return

        if range_header:
            start = parse_range(range_header)
            if start is None or start >= TOTAL:
                resp = "HTTP/1.1 416 Range Not Satisfiable\r\nContent-Length: 0\r\n\r\n"
                conn.sendall(resp.encode('ascii'))
                return
            body = DATA[start:]
            headers = (
                "HTTP/1.1 206 Partial Content\r\n"
                f"Content-Range: bytes {start}-{TOTAL-1}/{TOTAL}\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Content-Type: application/octet-stream\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            conn.sendall(headers.encode('ascii'))
            # send in chunks to simulate streaming
            idx = 0
            CH = 64 * 1024
            while idx < len(body):
                end = idx + CH
                conn.sendall(body[idx:end])
                idx = end
            return
        else:
            # initial full GET - simulate truncated transfer
            headers = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Length: {TOTAL}\r\n"
                "Content-Type: application/octet-stream\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            conn.sendall(headers.encode('ascii'))
            # send only FIRST_SEND bytes then close
            sent = 0
            CH = 32 * 1024
            while sent < FIRST_SEND:
                tosend = min(CH, FIRST_SEND - sent)
                conn.sendall(DATA[sent:sent+tosend])
                sent += tosend
            # close to simulate truncated download
            return
    finally:
        conn.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    s.settimeout(0.5)
    print(f"Serving {EXE_PATH} and {VERSIONS_PATH} on http://{HOST}:{PORT}")
    try:
        while True:
            try:
                conn, addr = s.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        try:
            s.close()
        except OSError:
            pass

if __name__ == "__main__":
    main()
