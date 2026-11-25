#!/usr/bin/env python3
"""Measure five anonymous GETs per page. Pass the canonical detail path for a specific place."""
import argparse
from collections import Counter
from http.client import HTTPException, HTTPResponse
import math
from statistics import median
import sys
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPHandler, HTTPRedirectHandler, HTTPSHandler, Request, build_opener


DEFAULT_PATHS = (
    "/", "/ru/", "/ru/catalog/", "/ru/events/", "/ru/specialists/", "/ru/catalog/dzudo-dlya-detey-v-baku/",
)
SAMPLES = 5


class TimedResponse(HTTPResponse):
    def begin(self):
        if self.headers is None:
            # The first socket byte is already available when peek returns. Waiting
            # for urlopen to return would also count the rest of the HTTP headers.
            self.fp.peek(1)
            self.first_byte_at = perf_counter()
        super().begin()


class TimingHandler(HTTPSHandler, HTTPHandler):
    def do_open(self, http_class, req, **options):
        def connect(*args, **kwargs):
            connection = http_class(*args, **kwargs)
            connection.response_class = TimedResponse
            return connection

        return super().do_open(connect, req, **options)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def durations(header):
    values = {}
    for metric in header.split(","):
        name, *parameters = metric.strip().split(";")
        if name not in ("app", "db"):
            continue
        for parameter in parameters:
            key, _, raw = parameter.strip().partition("=")
            if key == "dur":
                try:
                    value = float(raw)
                except ValueError:
                    continue
                if math.isfinite(value) and value >= 0:
                    values[name] = value
    return values


def sample(opener, url):
    request = Request(url, headers={"Accept-Encoding": "identity"})
    started = perf_counter()
    with opener.open(request, timeout=15) as response:
        if response.status != 200 or response.headers.get_content_type() not in ("text/html", "application/xhtml+xml"):
            raise ValueError(f"expected HTML 200, got {response.status} {response.headers.get_content_type()}")
        ttfb = (response.first_byte_at - started) * 1000
        return ttfb, len(response.read()), durations(response.headers.get("Server-Timing", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8000", help="Base URL for relative page paths")
    parser.add_argument("paths", nargs="*", help="Page paths or absolute HTTP(S) URLs")
    args = parser.parse_args()
    opener = build_opener(TimingHandler(), NoRedirect())
    print("URL\tGETs\tTTFB median (ms)\tHTML median (bytes)\tServer-Timing (medians, ms)")
    success = True
    for path in args.paths or DEFAULT_PATHS:
        url = urljoin(args.base.rstrip("/") + "/", path)
        if urlsplit(url).scheme not in ("http", "https"):
            parser.error(f"expected an HTTP(S) URL: {path}")
        samples = []
        errors = Counter()
        for _ in range(SAMPLES):
            try:
                samples.append(sample(opener, url))
            except HTTPError as exc:
                errors[f"HTTP {exc.code}"] += 1
                exc.close()
            except (OSError, HTTPException, ValueError) as exc:
                errors[str(exc)] += 1
        if errors:
            success = False
            print(f"{path}\t{len(samples)}/{SAMPLES}\t-\t-\t-")
            for message, count in errors.items():
                print(f"{path}: {count} × {message}", file=sys.stderr)
            continue
        ttfb, sizes, timings = zip(*samples)
        if all("app" in timing and "db" in timing for timing in timings):
            header = ", ".join(f"{key};dur={median(t[key] for t in timings):.3f}" for key in ("app", "db"))
        else:
            measured = sum("app" in timing and "db" in timing for timing in timings)
            header = f"unavailable ({measured}/{SAMPLES} complete headers)"
        print(f"{path}\t{len(samples)}/{SAMPLES}\t{median(ttfb):.3f}\t{median(sizes)}\t{header}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
