/*
 * Gestión de consentimiento de cookies.
 *
 * - La elección se guarda en una cookie propia "cookie_consent" (1 año).
 * - Los contenidos de terceros (YouTube, Google Maps) NO se cargan hasta que
 *   el usuario acepta: en las plantillas llevan data-consent-src en lugar de src.
 * - Si rechaza, en su lugar se muestra un aviso con un botón para aceptar.
 * - El enlace "Configurar cookies" (#cookie-settings) reabre el banner.
 */
(function () {
    "use strict";

    var COOKIE_NAME = "cookie_consent";
    var MAX_AGE = 60 * 60 * 24 * 365; // 1 año

    function readConsent() {
        var match = document.cookie.match(new RegExp("(?:^|; )" + COOKIE_NAME + "=([^;]*)"));
        if (!match) return null;
        try {
            var value = JSON.parse(decodeURIComponent(match[1]));
            return value && value.v === 1 ? value : null;
        } catch (e) {
            return null;
        }
    }

    function saveConsent(thirdParty) {
        var value = encodeURIComponent(JSON.stringify({ v: 1, third: thirdParty, ts: Date.now() }));
        var secure = location.protocol === "https:" ? "; Secure" : "";
        document.cookie = COOKIE_NAME + "=" + value + "; Max-Age=" + MAX_AGE + "; Path=/; SameSite=Lax" + secure;
    }

    function embeds() {
        return Array.prototype.slice.call(document.querySelectorAll("iframe[data-consent-src]"));
    }

    function removePlaceholder(iframe) {
        var prev = iframe.previousElementSibling;
        if (prev && prev.classList.contains("embed-placeholder")) prev.remove();
    }

    // Acepta: carga los contenidos de terceros.
    function loadEmbeds() {
        embeds().forEach(function (iframe) {
            removePlaceholder(iframe);
            iframe.classList.remove("consent-blocked");
            if (!iframe.getAttribute("src")) iframe.setAttribute("src", iframe.dataset.consentSrc);
        });
    }

    // Rechaza o aún no decidió: oculta el iframe y muestra un aviso en su lugar.
    function blockEmbeds(onAccept) {
        embeds().forEach(function (iframe) {
            var prev = iframe.previousElementSibling;
            if (prev && prev.classList.contains("embed-placeholder")) return;

            var service = iframe.dataset.consentService || "terceros";
            var cover = window.getComputedStyle(iframe).position === "absolute";

            var box = document.createElement("div");
            box.className = "embed-placeholder" + (cover ? " embed-placeholder--cover" : "");

            var text = document.createElement("p");
            text.textContent = "Para ver este contenido de " + service + " necesitas aceptar las cookies de terceros.";

            var button = document.createElement("button");
            button.type = "button";
            button.className = "btn btn-warning btn-sm";
            button.textContent = "Aceptar cookies";
            button.addEventListener("click", onAccept);

            box.appendChild(text);
            box.appendChild(button);
            iframe.classList.add("consent-blocked");
            iframe.parentNode.insertBefore(box, iframe);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var banner = document.getElementById("cookie-banner");
        var acceptBtn = document.getElementById("accept-cookies");
        var rejectBtn = document.getElementById("reject-cookies");
        var settingsLink = document.getElementById("cookie-settings");

        // Limpia la clave antigua (el banner anterior usaba localStorage).
        try { localStorage.removeItem("cookieConsent"); } catch (e) { /* sin acceso */ }

        function accept() {
            saveConsent(true);
            banner.hidden = true;
            loadEmbeds();
        }

        function reject() {
            var before = readConsent();
            saveConsent(false);
            banner.hidden = true;
            // Si ya había aceptado, hay iframes cargados: se recarga para descargarlos.
            if (before && before.third) {
                location.reload();
            } else {
                blockEmbeds(accept);
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

        var consent = readConsent();
        if (!consent) banner.hidden = false;

        if (consent && consent.third) {
            loadEmbeds();
        } else {
            blockEmbeds(accept);
        }
    });
})();
