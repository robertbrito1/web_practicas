/*
 * Gestión de consentimiento de cookies.
 *
 * - La elección se guarda en una cookie propia "cookie_consent" (1 año).
 * - Los contenidos de terceros NO se cargan hasta que el usuario acepta:
 *     · iframes (YouTube, Google Maps): llevan data-consent-src en lugar de src.
 *     · scripts (Elfsight, reseñas de Google): el contenedor lleva
 *       data-consent-script y el script se añade solo tras aceptar.
 * - Si rechaza, en su lugar se muestra un aviso con un botón para aceptar.
 * - El enlace "Configurar cookies" (#cookie-settings) reabre el banner.
 */
(function () {
    "use strict";

    let COOKIE_NAME = "cookie_consent";
    let MAX_AGE = 60 * 60 * 24 * 365; // 1 año

    function readConsent() {
        let match = document.cookie.match(new RegExp("(?:^|; )" + COOKIE_NAME + "=([^;]*)"));
        if (!match) return null;
        try {
            let value = JSON.parse(decodeURIComponent(match[1]));
            return value && value.v === 1 ? value : null;
        } catch (e) {
            return null;
        }
    }

    function saveConsent(thirdParty) {
        let value = encodeURIComponent(JSON.stringify({ v: 1, third: thirdParty, ts: Date.now() }));
        let secure = location.protocol === "https:" ? "; Secure" : "";
        document.cookie = COOKIE_NAME + "=" + value + "; Max-Age=" + MAX_AGE + "; Path=/; SameSite=Lax" + secure;
    }

    function all(selector) {
        return Array.prototype.slice.call(document.querySelectorAll(selector));
    }

    // Aviso que sustituye al contenido de terceros mientras no haya consentimiento.
    function makePlaceholder(service, cover, onAccept) {
        let box = document.createElement("div");
        box.className = "embed-placeholder" + (cover ? " embed-placeholder--cover" : "");

        let text = document.createElement("p");
        text.textContent = "Para ver este contenido de " + service + " necesitas aceptar las cookies de terceros.";

        let button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-warning btn-sm";
        button.textContent = "Aceptar cookies";
        button.addEventListener("click", onAccept);

        box.appendChild(text);
        box.appendChild(button);
        return box;
    }

    // ---- iframes -----------------------------------------------------------

    function removePlaceholderBefore(iframe) {
        let prev = iframe.previousElementSibling;
        if (prev && prev.classList.contains("embed-placeholder")) prev.remove();
    }

    function loadEmbeds() {
        all("iframe[data-consent-src]").forEach(function (iframe) {
            removePlaceholderBefore(iframe);
            iframe.classList.remove("consent-blocked");
            if (!iframe.getAttribute("src")) iframe.setAttribute("src", iframe.dataset.consentSrc);
        });
    }

    function blockEmbeds(onAccept) {
        all("iframe[data-consent-src]").forEach(function (iframe) {
            let prev = iframe.previousElementSibling;
            if (prev && prev.classList.contains("embed-placeholder")) return;

            let cover = window.getComputedStyle(iframe).position === "absolute";
            iframe.classList.add("consent-blocked");
            iframe.parentNode.insertBefore(
                makePlaceholder(iframe.dataset.consentService || "terceros", cover, onAccept),
                iframe
            );
        });
    }

    // ---- scripts de terceros (p. ej. Elfsight) ------------------------------

    function loadScripts() {
        all("[data-consent-script]").forEach(function (box) {
            let old = box.querySelector(".embed-placeholder");
            if (old) old.remove();
            box.classList.remove("consent-pending");
            box.classList.add("consent-loaded");

            if (box.dataset.scriptLoaded) return;
            box.dataset.scriptLoaded = "1";

            let script = document.createElement("script");
            script.src = box.dataset.consentScript;
            script.async = true;
            document.body.appendChild(script);
        });
    }

    function blockScripts(onAccept) {
        all("[data-consent-script]").forEach(function (box) {
            if (box.querySelector(".embed-placeholder")) return;
            box.classList.remove("consent-loaded");
            box.classList.add("consent-pending");
            box.insertBefore(
                makePlaceholder(box.dataset.consentService || "terceros", false, onAccept),
                box.firstChild
            );
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        let banner = document.getElementById("cookie-banner");
        let acceptBtn = document.getElementById("accept-cookies");
        let rejectBtn = document.getElementById("reject-cookies");
        let settingsLink = document.getElementById("cookie-settings");

        // Limpia la clave antigua (el banner anterior usaba localStorage).
        try { localStorage.removeItem("cookieConsent"); } catch (e) { /* sin acceso */ }

        function accept() {
            saveConsent(true);
            banner.hidden = true;
            loadEmbeds();
            loadScripts();
        }

        function reject() {
            let before = readConsent();
            saveConsent(false);
            banner.hidden = true;
            // Si ya había aceptado, hay contenido de terceros cargado: se recarga para descargarlo.
            if (before && before.third) {
                location.reload();
            } else {
                blockEmbeds(accept);
                blockScripts(accept);
            }
        }

        acceptBtn.addEventListener("click", accept);
        rejectBtn.addEventListener("click", reject);

        if (settingsLink) {
            settingsLink.addEventListener("click", function (event) {
                event.preventDefault();
                banner.hidden = false;
                acceptBtn.focus();
            });
        }

        let consent = readConsent();
        if (!consent) banner.hidden = false;

        if (consent && consent.third) {
            loadEmbeds();
            loadScripts();
        } else {
            blockEmbeds(accept);
            blockScripts(accept);
        }
    });
})();
