import json
import logging
import os
import platform
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-12s %(lineno)d %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger_name = "{} :: {}".format(__file__, __name__)
logger = logging.getLogger(logger_name)


@dataclass
class TestResult:
    ping: float = 0.0
    download_speed: float = 0.0
    download_size: float = 0.0
    _download_sizes: List[float] = field(default_factory=list)


def run_download_speed_test(
    url: str, result: TestResult, idx: int, stop_event: threading.Event
):
    """Count the amount of data successfully downloaded."""
    downloaded = 0
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            while not stop_event.is_set():
                chunk = resp.read(56)
                if not chunk:
                    break
                downloaded += len(chunk)
    except Exception as e:
        logger.error("Error downloading from {}: {}".format(url, e))
        downloaded = 0
    result._download_sizes[idx] = downloaded


def run_ping_test(host: str, result: TestResult, stop_event: threading.Event):
    """Ping a URL to measure response time."""
    system = platform.system().lower()
    if system == "windows":
        ping_cmd = ["ping", "-n", "4", host]
    else:
        ping_cmd = ["ping", "-c", "4", host]
    try:
        proc = subprocess.run(
            ping_cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = proc.stdout

        avg_ping = None
        if "Average =" in output:  # Windows
            avg_ping = float(output.split("Average =")[-1].split("ms")[0].strip())
        elif "avg" in output:  # Unix
            avg_line = [
                line for line in output.splitlines() if "avg" in line or "rtt" in line
            ]
            if avg_line:
                avg_val = avg_line[0].split("/")[4]
                avg_ping = float(avg_val)
        result.ping = avg_ping if avg_ping is not None else 0.0
    except Exception as e:
        logger.error("Ping error for {}: {}".format(host, e))
        result.ping = 0.0


def _find_from(text: str, start: str, until: str) -> str:
    start_find = text.find(start)
    start_length = len(start)
    end_find = text.find(until, start_find + start_length)
    if -1 in (start_find, end_find):
        return ""
    else:
        start_idx = start_find + start_length
        end_idx = end_find
        return text[start_idx:end_idx]


def _get_token() -> str:
    url = "https://fast.com"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        resp = r.read().decode()
    js = _find_from(resp, '<script src="', '"')

    js_url = url + js
    js_req = urllib.request.Request(js_url)
    with urllib.request.urlopen(js_req) as jr:
        jsresp = jr.read().decode()

    token = _find_from(jsresp, 'token:"', '"')
    return token


def run_test() -> TestResult:
    """Create threads for speedtest and return results."""
    timeout = 30.0
    token = _get_token()

    params = {"https": "true", "urlCount": "3", "token": token}
    query_str = urllib.parse.urlencode(params)

    api_base = "https://api.fast.com"
    url = "{}/netflix/speedtest/v2?{}".format(api_base, query_str)

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        resp = r.read().decode()
    resp_json = json.loads(resp)

    stop_event = threading.Event()
    result = TestResult()
    num_targets = len(resp_json["targets"])
    result._download_sizes = [0] * num_targets

    # Start ping thread
    ping_thread = threading.Thread(
        target=run_ping_test,
        args=("fast.com", result, stop_event),
    )
    ping_thread.start()

    # Start download threads
    download_threads = []
    download_start_time = time.time()
    for idx, target in enumerate(resp_json["targets"]):
        t = threading.Thread(
            target=run_download_speed_test,
            args=(target["url"], result, idx, stop_event),
        )
        download_threads.append(t)
        t.start()

    # Wait for timeout or all download threads to finish
    for t in download_threads:
        t.join(timeout=timeout)
    duration = time.time() - download_start_time
    result.download_size = sum(result._download_sizes)
    # Calculate download speed in Mbps
    result.download_speed = result.download_size / duration * 8 / 1024 / 1024
    logger.info("Run time: {:.2f} seconds".format(duration))

    # Wait for ping thread to finish
    ping_thread.join(timeout=timeout)

    stop_event.set()  # Signal threads to stop if not finished

    return result


def save_result(result: TestResult):
    script_folder = Path(__file__).resolve().parent
    result_file_path = script_folder / "internet_speed_test_result.csv"
    logger.info("Saving result to {}".format(result_file_path))
    offset = -time.timezone if time.localtime().tm_isdst == 0 else -time.altzone
    local_time = datetime.now(timezone(timedelta(seconds=offset)))
    local_time = local_time.replace(microsecond=0)
    with open(result_file_path, "a") as f:
        f.write(
            "{},{},{},{}\n".format(
                local_time.isoformat(),
                result.ping,
                result.download_speed,
                result.download_size,
            )
        )


def main():
    """Main function to run the download speed test."""
    while True:
        try:
            result = run_test()
            logger.info(
                "Approximate download speed: {:.2f} Mbps".format(result.download_speed)
            )
            logger.info(
                "Total download size: {:.2f} MB".format(
                    result.download_size / 1024 / 1024
                )
            )
            logger.info("Approximate ping: {:.2f} ms".format(result.ping))
            save_result(result)
        except Exception as e:
            logger.error("Error running speed test: {}".format(e))
        next_run = datetime.now() + timedelta(minutes=30)
        logger.info(
            "Next test will run at {}".format(next_run.strftime("%Y-%m-%d %H:%M:%S"))
        )
        time.sleep(1800)  # Wait for 30 minutes before next run


def setup():
    """Create an autostart batch file for Windows."""
    if platform.system().lower() == "windows":
        logger.info("Setting up autostart for Windows.")
        script_path = Path(__file__).resolve()
        startup_folder = (
            Path(os.getenv("APPDATA")) / "Microsoft/Windows/Start Menu/Programs/Startup"
        )
        startup_bat = startup_folder / "internet_speed_test.bat"
        bat_content = f'@echo off\npython "{script_path}" --startup\n'
        with open(startup_bat, "w") as bat_file:
            bat_file.write(bat_content)
    else:
        logger.info(
            "Autostart setup is not implemented for this OS. Please setup manually."
        )


if __name__ == "__main__":
    logging.info("Starting internet speed monitoring.")
    setup()
    if "--startup" in os.sys.argv:
        # If auto-started after system boot, wait for 5 minutes before running the test
        next_run = datetime.now() + timedelta(minutes=5)
        logger.info(
            "Next test will run at {}".format(next_run.strftime("%Y-%m-%d %H:%M:%S"))
        )
        time.sleep(300)
    main()
