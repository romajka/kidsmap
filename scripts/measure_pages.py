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
    "/", "/ru/", "/ru/catalog/", "/tedbirler/", "/ru/afisha/", "/en/events/", "/ru/specialists/", "/ru/catalog/dzudo-dlya-detey-v-baku/",
)
DEFAULT_REDIRECTS = (("/events/", "/tedbirler/"), ("/ru/events/", "/ru/afisha/"))
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


def sample(opener, url, redirect_to=None):
    request = Request(url, headers={"Accept-Encoding": "identity"})
    started = perf_counter()
    try:
        response = opener.open(request, timeout=15)
    except HTTPError as exc:
        if redirect_to is None or exc.code != 301:
            raise
        with exc:
            location = exc.headers.get("Location", "")
            if not location or urljoin(url, location) != redirect_to:
                raise ValueError(f"unexpected redirect target: {location!r}")
            ttfb = (exc.fp.first_byte_at - started) * 1000
            return ttfb, len(exc.read()), durations(exc.headers.get("Server-Timing", ""))
    with response:
        if redirect_to:
            raise ValueError(f"expected 301 redirect, got {response.status}")
        if response.status != 200 or response.headers.get_content_type() not in ("text/html", "application/xhtml+xml"):
            raise ValueError(f"expected HTML 200, got {response.status} {response.headers.get_content_type()}")
        ttfb = (response.first_byte_at - started) * 1000
        return ttfb, len(response.read()), durations(response.headers.get("Server-Timing", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8000", help="Base URL for relative page paths")
    parser.add_argument("paths", nargs="*", help="Page paths or absolute HTTP(S) URLs")
    parser.add_argument("--redirect", nargs=2, action="append", metavar=("OLD", "NEW"),
                        help="Measure a permanent redirect separately without following it")
    args = parser.parse_args()
    opener = build_opener(TimingHandler(), NoRedirect())
    print("URL\tGETs\tTTFB median (ms)\tHTML median (bytes)\tServer-Timing (medians, ms)")
    success = True
    default_run = not (args.paths or args.redirect)
    rows = [(path, None) for path in (DEFAULT_PATHS if default_run else args.paths)]
    rows.extend(DEFAULT_REDIRECTS if default_run else (args.redirect or ()))
    for path, redirect_to in rows:
        url = urljoin(args.base.rstrip("/") + "/", path)
        if urlsplit(url).scheme not in ("http", "https"):
            parser.error(f"expected an HTTP(S) URL: {path}")
        target = urljoin(args.base.rstrip("/") + "/", redirect_to) if redirect_to else None
        label = f"{path} → {redirect_to} (301)" if target else path
        samples = []
        errors = Counter()
        for _ in range(SAMPLES):
            try:
                samples.append(sample(opener, url, target))
            except HTTPError as exc:
                errors[f"HTTP {exc.code}"] += 1
                exc.close()
            except (OSError, HTTPException, ValueError) as exc:
                errors[str(exc)] += 1
        if errors:
            success = False
            print(f"{label}\t{len(samples)}/{SAMPLES}\t-\t-\t-")
            for message, count in errors.items():
                print(f"{path}: {count} × {message}", file=sys.stderr)
            continue
        ttfb, sizes, timings = zip(*samples)
        if all("app" in timing and "db" in timing for timing in timings):
            header = ", ".join(f"{key};dur={median(t[key] for t in timings):.3f}" for key in ("app", "db"))
        else:
            measured = sum("app" in timing and "db" in timing for timing in timings)
            header = f"unavailable ({measured}/{SAMPLES} complete headers)"
        print(f"{label}\t{len(samples)}/{SAMPLES}\t{median(ttfb):.3f}\t{median(sizes)}\t{header}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
