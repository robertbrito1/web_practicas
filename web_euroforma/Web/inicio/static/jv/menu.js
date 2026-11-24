/*
 * Menú de hamburguesa (móvil/tablet).
 *
 * El menú funciona con un checkbox (#menu-toggle) y CSS. Este script añade el
 * comportamiento que faltaba: se cierra al tocar fuera, con Escape, al elegir
 * un enlace y al pasar a pantalla de escritorio; además funciona con teclado.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        let toggle = document.getElementById("menu-toggle");
        let icon = document.querySelector(".menu-icon");
        let navbar = document.querySelector(".navbar");
        if (!toggle || !icon || !navbar) return;

        function sync() {
            icon.setAttribute("aria-expanded", toggle.checked ? "true" : "false");
            icon.setAttribute("aria-label", toggle.checked ? "Cerrar menú" : "Abrir menú");
        }

        function close() {
            if (!toggle.checked) return;
            toggle.checked = false;
            sync();
        }

        toggle.addEventListener("change", sync);

        // Teclado: Enter o Espacio sobre el icono abren y cierran el menú.
        icon.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                toggle.checked = !toggle.checked;
                sync();
            }
        });

        // Tocar o hacer clic fuera del menú lo cierra.
        document.addEventListener("click", function (event) {
            if (toggle.checked && !navbar.contains(event.target)) close();
        });

        // Escape cierra el menú y devuelve el foco al icono.
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && toggle.checked) {
                close();
                icon.focus();
            }
        });

        // Elegir un enlace cierra el menú.
        navbar.querySelectorAll(".menu a").forEach(function (link) {
            link.addEventListener("click", close);
        });

        // Al pasar a escritorio (el menú pasa a estar en línea) se deja cerrado.
        window.matchMedia("(min-width: 769px)").addEventListener("change", close);
    });
})();
