(() => {
    const storageKey = "casrce_tab_session";
    const sessionHeader = "X-CASRCE-Tab-Session";
    const sessionQuery = "tab_session_id";
    const bootstrapQuery = "tab_session_bootstrap";
    const browserStorageKey = "casrce_browser_id";
    const browserHeader = "X-CASRCE-Browser-Id";
    const serverSessionId = window.CASRCE_TAB_SESSION_ID;

    function createSessionId() {
        if (window.crypto && typeof window.crypto.randomUUID === "function") {
            return window.crypto.randomUUID().replace(/-/g, "");
        }

        const values = new Uint8Array(16);
        window.crypto.getRandomValues(values);
        return Array.from(values, value => value.toString(16).padStart(2, "0")).join("");
    }

    let sessionId = serverSessionId;
    const pageUrl = new URL(window.location.href);
    const urlSessionId = pageUrl.searchParams.get(sessionQuery);
    const isBootstrapNavigation = pageUrl.searchParams.has(bootstrapQuery);
    let storedSessionId = null;
    let sessionStorageAvailable = true;
    try {
        storedSessionId = sessionStorage.getItem(storageKey);
    } catch (error) {
        sessionStorageAvailable = false;
        console.error("No fue posible leer la sesión independiente de esta pestaña:", error);
    }

    if (
        sessionStorageAvailable
        && storedSessionId
        && storedSessionId !== (urlSessionId || serverSessionId)
    ) {
        document.documentElement.style.visibility = "hidden";
        pageUrl.searchParams.set(sessionQuery, storedSessionId);
        pageUrl.searchParams.delete(bootstrapQuery);
        window.location.replace(pageUrl.href);
        return;
    }

    try {
        if (!sessionId) {
            sessionId = urlSessionId || storedSessionId;
        }
        if (!sessionId) {
            sessionId = createSessionId();
        }
        sessionStorage.setItem(storageKey, sessionId);

        if (isBootstrapNavigation) {
            pageUrl.searchParams.delete(bootstrapQuery);
            window.history.replaceState(
                window.history.state,
                "",
                pageUrl.href
            );
        }
    } catch (error) {
        console.error("No fue posible mantener la sesión independiente de esta pestaña:", error);
    }

    window.CASRCE_TAB_SESSION_ID = sessionId;

    let browserId;
    try {
        browserId = localStorage.getItem(browserStorageKey);
        if (!browserId) {
            browserId = createSessionId();
            localStorage.setItem(browserStorageKey, browserId);
        }
    } catch (error) {
        console.error("No fue posible identificar este navegador:", error);
    }
    window.CASRCE_BROWSER_ID = browserId;

    function urlForCurrentTab(value) {
        const url = new URL(value, window.location.href);
        if (url.origin === window.location.origin && sessionId) {
            url.searchParams.set(sessionQuery, sessionId);
        }
        return url;
    }

    window.CASRCE_TAB_NAVIGATE = value => {
        window.location.assign(urlForCurrentTab(value).href);
    };

    function saveSessionId(response) {
        const newSessionId = response.headers.get(sessionHeader);
        if (!newSessionId) {
            return;
        }

        sessionId = newSessionId;
        window.CASRCE_TAB_SESSION_ID = sessionId;
        try {
            sessionStorage.setItem(storageKey, sessionId);
        } catch (error) {
            console.error("No fue posible actualizar la sesión de esta pestaña:", error);
        }
    }

    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
        init = init || {};
        const requestUrl = new URL(
            input instanceof Request ? input.url : input,
            window.location.href
        );
        const headers = new Headers(
            input instanceof Request ? input.headers : undefined
        );
        new Headers(init.headers).forEach((value, name) => {
            headers.set(name, value);
        });
        if (requestUrl.origin === window.location.origin && sessionId) {
            headers.set(sessionHeader, sessionId);
        }
        if (requestUrl.origin === window.location.origin && browserId) {
            headers.set(browserHeader, browserId);
        }

        return originalFetch(input, { ...init, headers }).then(response => {
            if (requestUrl.origin === window.location.origin) {
                saveSessionId(response);
            }
            return response;
        });
    };

    function decorateLink(link) {
        const rawHref = link.getAttribute("href");
        if (!rawHref || rawHref.startsWith("#") || rawHref.startsWith("javascript:")) {
            return;
        }

        const url = new URL(rawHref, window.location.href);
        if (url.origin !== window.location.origin) {
            return;
        }

        if (link.target === "_blank") {
            url.searchParams.delete(sessionQuery);
            link.relList.add("noopener");
        } else if (sessionId) {
            url.searchParams.set(sessionQuery, sessionId);
        }
        if (url.pathname === "/cerrar_sesion/" && browserId) {
            url.searchParams.set("browser_auth_id", browserId);
        }
        link.href = url.href;
    }

    function decorateForm(form) {
        const rawAction = form.getAttribute("action") || window.location.href;
        const url = new URL(rawAction, window.location.href);
        if (url.origin === window.location.origin && sessionId) {
            url.searchParams.set(sessionQuery, sessionId);
            form.action = url.href;
        }
    }

    function decorateDocument() {
        document.querySelectorAll("a[href]").forEach(decorateLink);
        document.querySelectorAll("form").forEach(decorateForm);
    }

    document.addEventListener("click", event => {
        const link = event.target.closest("a[href]");
        if (link) {
            decorateLink(link);
        }
    }, true);
    document.addEventListener("submit", event => decorateForm(event.target), true);
    document.addEventListener("DOMContentLoaded", decorateDocument);
    new MutationObserver(decorateDocument).observe(document.documentElement, {
        childList: true,
        subtree: true
    });
})();
