#!/usr/bin/env python3
"""Quest 핫리로드용 개발 서버 (표준 라이브러리만 사용).

- Unity Live 폴더의 *.glb 를 HTTP로 서빙
- GET /version/<name>  → 파일 mtime 기반 버전 문자열 (Quest가 폴링)
- GET /asset/<name>    → GLB 바이너리
- adb reverse 를 주기적으로 걸어서 Quest에서 http://127.0.0.1:PORT 로 PC에 접속 (USB, Wi-Fi 설정 불필요)
- --launch 패키지명을 주면 서버 시작 시 Quest 앱 실행

사용: python live_server.py --dir "C:/Projects/MyMR/Assets/Characters/Live" --launch com.me.mrapp
"""
import argparse
import os
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

ARGS = None


def adb(*cmd):
    exe = shutil.which("adb")
    if not exe:
        return None
    return subprocess.run([exe, *cmd], capture_output=True, text=True)


def keep_adb_reverse(port):
    # 헤드셋을 뽑았다 꽂아도 다시 연결되도록 5초마다 재설정
    while True:
        r = adb("reverse", f"tcp:{port}", f"tcp:{port}")
        if r is None:
            print("[live] adb가 PATH에 없습니다. Android platform-tools를 설치하세요.")
            return
        time.sleep(5)


class Handler(BaseHTTPRequestHandler):
    def _file(self, name):
        name = os.path.basename(unquote(name))  # 경로 탈출 방지
        path = os.path.join(ARGS.dir, name)
        return path if os.path.isfile(path) else None

    def do_GET(self):
        parts = self.path.split("?")[0].strip("/").split("/", 1)
        if len(parts) != 2 or parts[0] not in ("version", "asset"):
            return self.send_error(404)
        path = self._file(parts[1])
        if not path:
            return self.send_error(404, "asset not found")

        if parts[0] == "version":
            st = os.stat(path)
            body = f"{st.st_mtime_ns}-{st.st_size}".encode()
            ctype = "text/plain"
        else:
            with open(path, "rb") as f:
                body = f.read()
            ctype = "model/gltf-binary"

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        if "/asset/" in (a[0] if a else ""):
            print("[live] 전송:", a[0])


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Blender가 GLB를 export하는 Unity Live 폴더")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--launch", help="시작 시 실행할 Quest 앱 패키지명")
    ARGS = ap.parse_args()

    threading.Thread(target=keep_adb_reverse, args=(ARGS.port,), daemon=True).start()
    if ARGS.launch:
        time.sleep(1)
        adb("shell", "monkey", "-p", ARGS.launch, "-c", "android.intent.category.LAUNCHER", "1")

    print(f"[live] {ARGS.dir} 를 http://127.0.0.1:{ARGS.port} 로 서빙 중 (Ctrl+C 종료)")
    ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
