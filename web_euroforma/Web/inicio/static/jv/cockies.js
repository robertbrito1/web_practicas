document.addEventListener("DOMContentLoaded", function () {
    const cookieBanner = document.getElementById("cookie-banner");
    const acceptBtn = document.getElementById("accept-cookies");
    const rejectBtn = document.getElementById("reject-cookies");

    if (!localStorage.getItem("cookieConsent")) {
        cookieBanner.style.display = "block";
    }

    acceptBtn.addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "accepted");
        cookieBanner.style.display = "none";
    });

    rejectBtn.addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "rejected");
        cookieBanner.style.display = "none";
    });
});
