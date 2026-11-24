/*
 * Asistente de chat (widget de la página de inicio).
 *
 * Seguridad:
 *  - Todo el texto (del usuario y del asistente) se inserta con createTextNode, nunca con
 *    innerHTML: no se puede inyectar HTML ni scripts.
 *  - Los enlaces solo se crean para URLs https:// y rutas internas conocidas.
 *  - La petición lleva el token CSRF en la cabecera X-CSRFToken.
 *
 * El servidor (chat/views.py) responde con el FAQ y, si estuviera activada, con IA.
 */
(function () {
    "use strict";

    // Enlaces permitidos: https://... o rutas internas de la web.
    let PATRON_ENLACES = /(https?:\/\/[^\s)]+|\/(?:contacto|equipo|nosotros|preguntas|rsc|politicas|avisos|cockies)\/?)/g;
    let URL_CHAT = "/api/chat/";
    let MAX_HISTORIAL = 6;

    document.addEventListener("DOMContentLoaded", function () {
        let formulario = document.getElementById("chat-form");
        let caja = document.getElementById("chat-box");
        let entrada = document.getElementById("user-input");
        let sugerencias = document.getElementById("chat-sugerencias");
        let campoToken = document.querySelector("#chat-widget input[name=csrfmiddlewaretoken]");
        if (!formulario || !caja || !entrada || !sugerencias || !campoToken) return;  // otras páginas

        let boton = formulario.querySelector("button[type=submit]");
        let historial = [];
        let ocupado = false;

        function bajar() {
            caja.scrollTop = caja.scrollHeight;  // solo la caja del chat, no la página
        }

        // Texto con saltos de línea (CSS pre-line) y enlaces seguros, sin innerHTML.
        function escribirTexto(elemento, texto) {
            let partes = texto.split(PATRON_ENLACES);
            partes.forEach(function (parte, indice) {
                if (indice % 2 === 0) {
                    if (parte) elemento.appendChild(document.createTextNode(parte));
                    return;
                }
                let enlace = document.createElement("a");
                enlace.textContent = parte;
                enlace.href = parte;
                if (parte.indexOf("http") === 0) {
                    enlace.target = "_blank";
                    enlace.rel = "noopener noreferrer";
                }
                elemento.appendChild(enlace);
            });
        }

        function anadirMensaje(rol, texto) {
            let fila = document.createElement("div");
            fila.className = "chat-msg chat-msg--" + rol;
            let burbuja = document.createElement("div");
            burbuja.className = "chat-burbuja";
            escribirTexto(burbuja, texto);
            fila.appendChild(burbuja);
            caja.appendChild(fila);
            bajar();
            return fila;
        }

        function mostrarEscribiendo() {
            let fila = document.createElement("div");
            fila.className = "chat-msg chat-msg--bot";
            let burbuja = document.createElement("div");
            burbuja.className = "chat-burbuja chat-escribiendo";
            burbuja.setAttribute("aria-label", "El asistente está escribiendo");
            for (let i = 0; i < 3; i++) burbuja.appendChild(document.createElement("span"));
            fila.appendChild(burbuja);
            caja.appendChild(fila);
            bajar();
            return fila;
        }

        function pintarSugerencias(lista) {
            while (sugerencias.firstChild) sugerencias.removeChild(sugerencias.firstChild);
            (lista || []).forEach(function (texto) {
                let chip = document.createElement("button");
                chip.type = "button";
                chip.className = "chat-chip";
                chip.textContent = texto;
                sugerencias.appendChild(chip);
            });
        }

        function ocuparChat(estado) {
            ocupado = estado;
            entrada.disabled = estado;
            boton.disabled = estado;
            sugerencias.querySelectorAll("button").forEach(function (chip) { chip.disabled = estado; });
        }

        async function enviar(texto) {
            texto = (texto || "").trim();
            if (!texto || ocupado) return;

            let previo = historial.slice(-MAX_HISTORIAL);  // mensajes anteriores, sin el actual
            anadirMensaje("user", texto);
            entrada.value = "";
            ocuparChat(true);
            let escribiendo = mostrarEscribiendo();

            let respuesta = "Ha ocurrido un error. Inténtalo de nuevo en unos minutos.";
            let valido = false;
            let nuevasSugerencias = null;
            try {
                let r = await fetch(URL_CHAT, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": campoToken.value,
                    },
                    body: JSON.stringify({ message: texto, history: previo }),
                });
                let datos = null;
                try { datos = await r.json(); } catch (e) { /* respuesta sin JSON */ }
                if (datos && typeof datos.reply === "string") {
                    respuesta = datos.reply;
                    valido = r.ok;
                    if (Array.isArray(datos.suggestions)) nuevasSugerencias = datos.suggestions;
                } else if (r.status === 403) {
                    respuesta = "La sesión ha caducado. Recarga la página e inténtalo de nuevo.";
                }
            } catch (e) {
                respuesta = "No he podido conectar con el servidor. Comprueba tu conexión.";
            }

            escribiendo.remove();
            anadirMensaje("bot", respuesta);
            if (valido) {  // los errores no se guardan en el contexto de la conversación
                historial.push({ role: "user", content: texto }, { role: "assistant", content: respuesta });
                historial = historial.slice(-MAX_HISTORIAL);
            }
            if (nuevasSugerencias) pintarSugerencias(nuevasSugerencias);
            ocuparChat(false);
            entrada.focus({ preventScroll: true });
        }

        formulario.addEventListener("submit", function (evento) {
            evento.preventDefault();
            enviar(entrada.value);
        });

        // Delegación: sirve también para los botones que se crean después.
        sugerencias.addEventListener("click", function (evento) {
            let chip = evento.target.closest(".chat-chip");
            if (chip) enviar(chip.textContent);
        });

        anadirMensaje(
            "bot",
            "¡Hola! 👋 Soy el asistente virtual de FP Euroformac. Pregúntame por cursos, becas, sedes o inscripción, " +
            "o elige una de las preguntas de abajo."
        );
    });
})();
