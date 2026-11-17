"""Response policies for public service endpoints."""

from functools import wraps


def noindex_response(view):
    """Keep service responses, including method rejections, out of search."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return wrapped
