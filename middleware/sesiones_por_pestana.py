import re
from importlib import import_module
from secrets import compare_digest, token_urlsafe
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponseRedirect


TAB_SESSION_QUERY = "tab_session_id"
TAB_SESSION_BOOTSTRAP_QUERY = "tab_session_bootstrap"
TAB_SESSION_HEADER = "HTTP_X_CASRCE_TAB_SESSION"
TAB_SESSION_RESPONSE_HEADER = "X-CASRCE-Tab-Session"
TAB_SESSION_BOOTSTRAP_KEY = "_casrce_tab_session_bootstrap"
SESSION_KEY_PATTERN = re.compile(r"^[A-Za-z0-9]{8,40}$")


class SesionesPorPestanaMiddleware:
    """Uses a separate Django session store for each browser tab."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.session_store = import_module(settings.SESSION_ENGINE).SessionStore

    def __call__(self, request):
        if self._is_static_request(request):
            return self.get_response(request)

        session_id = next(
            (
                candidate
                for candidate in (
                    request.META.get(TAB_SESSION_HEADER),
                    request.GET.get(TAB_SESSION_QUERY),
                )
                if self._is_valid_session_id(candidate)
            ),
            None,
        )
        has_valid_session_id = session_id is not None
        is_document_navigation = (
            request.method in ("GET", "HEAD")
            and (
                request.headers.get("Sec-Fetch-Dest") == "document"
                or (
                    "text/html" in request.headers.get("Accept", "")
                    and not request.headers.get("X-CASRCE-Tab-Session")
                )
            )
        )

        if not session_id and not is_document_navigation:
            return self.get_response(request)

        shared_session = request.session
        bootstrap_token = None
        if session_id:
            tab_session = self.session_store(session_key=session_id)
        else:
            tab_session, bootstrap_token = self._create_tab_session(
                is_document_navigation
            )
            session_id = tab_session.session_key

        if is_document_navigation and request.GET.get(
            TAB_SESSION_BOOTSTRAP_QUERY
        ):
            expected_bootstrap = tab_session.pop(
                TAB_SESSION_BOOTSTRAP_KEY,
                None,
            )
            if not (
                expected_bootstrap
                and compare_digest(
                    expected_bootstrap,
                    request.GET[TAB_SESSION_BOOTSTRAP_QUERY],
                )
            ):
                tab_session, bootstrap_token = self._create_tab_session(True)
                session_id = tab_session.session_key
                has_valid_session_id = False
            else:
                bootstrap_token = None
        elif has_valid_session_id:
            bootstrap_token = None

        request.session = tab_session
        request.tab_session_id = session_id
        try:
            if not has_valid_session_id and is_document_navigation:
                response = HttpResponseRedirect(request.get_full_path())
                response[TAB_SESSION_RESPONSE_HEADER] = session_id
                response["Referrer-Policy"] = "no-referrer"
                self._preserve_session_in_redirect(request, response, session_id)
                self._append_bootstrap_token(response, bootstrap_token)
                return response

            response = self.get_response(request)

            if tab_session.session_key is None:
                tab_session.create()
            elif tab_session.modified:
                tab_session.save()

            session_id = tab_session.session_key
            response[TAB_SESSION_RESPONSE_HEADER] = session_id
            response["Referrer-Policy"] = "no-referrer"
            self._preserve_session_in_redirect(request, response, session_id)
            return response
        finally:
            request.session = shared_session

    def _create_tab_session(self, is_document_navigation):
        tab_session = self.session_store()
        bootstrap_token = None
        if is_document_navigation:
            bootstrap_token = token_urlsafe(24)
            tab_session[TAB_SESSION_BOOTSTRAP_KEY] = bootstrap_token
        tab_session.create()
        return tab_session, bootstrap_token

    @staticmethod
    def _is_valid_session_id(session_id):
        return bool(
            session_id
            and SESSION_KEY_PATTERN.fullmatch(session_id)
        )

    @staticmethod
    def _is_static_request(request):
        return any(
            url_prefix and request.path_info.startswith(url_prefix)
            for url_prefix in (settings.STATIC_URL, settings.MEDIA_URL)
        )

    @staticmethod
    def _preserve_session_in_redirect(request, response, session_id):
        if response.status_code not in (301, 302, 303, 307, 308):
            return

        location = response.get("Location")
        if not location:
            return

        parsed = urlsplit(location)
        if parsed.netloc and parsed.netloc != request.get_host():
            return

        query = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key not in (TAB_SESSION_QUERY, TAB_SESSION_BOOTSTRAP_QUERY)
        ]
        query.append((TAB_SESSION_QUERY, session_id))
        response["Location"] = urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
        )

    @staticmethod
    def _append_bootstrap_token(response, bootstrap_token):
        if not bootstrap_token or not response.get("Location"):
            return

        parsed = urlsplit(response["Location"])
        query = parse_qsl(parsed.query, keep_blank_values=True)
        query.append((TAB_SESSION_BOOTSTRAP_QUERY, bootstrap_token))
        response["Location"] = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(query),
                parsed.fragment,
            )
        )
