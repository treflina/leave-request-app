import { urlB64ToUint8Array, getCookie } from "./utils.js";

let registration, btnText, subBtn;

window.addEventListener("load", function () {
    subBtn = document.querySelector(".sub-btn");
    btnText = document.querySelector(".btn-text");

    // Do everything if the Browser Supports Service Worker
    if ("serviceWorker" in navigator) {
        const serviceWorker = document.querySelector('meta[name="sw"]').content;
        navigator.serviceWorker
            .register(serviceWorker)
            .then(function (reg) {
                registration = reg;
                if (subBtn) {
                    initialiseState(reg);
                }
            })
            .catch(console.log);
    }
    // If service worker not supported, show warning to the message box
    else {
        showMessage(
            gettext("Service workers are not supported in your browser.")
        );
    }

    // Once the service worker is registered set the initial state
    function initialiseState(reg) {
        // Are Notifications supported in the service worker?
        if (!reg.showNotification) {
            subBtn.setAttribute("aria-pressed", false);

            showMessage(
                gettext(
                    "Showing notifications are not supported in your browser."
                )
            );
            return;
        }

        // Check the current Notification permission.
        // If its denied, it's a permanent block until the
        // user changes the permission
        if (Notification.permission === "denied") {
            subBtn.disabled = false;
            subBtn.setAttribute("aria-pressed", false);
            showMessage(
                gettext("Push notifications are blocked by your browser.")
            );
            return;
        }

        // Check if push messaging is supported
        if (!("PushManager" in window)) {
            subBtn.disabled = false;
            subBtn.setAttribute("aria-pressed", false);
            showMessage(
                gettext("Push notifications are not available in your browser.")
            );
            return;
        };

        // We need to get subscription state for push notifications and send the information to server
        reg.pushManager.getSubscription().then(function (subscription) {
            //
            if (subscription) {
                subBtn.isPushEnabled = false;

                checkSubscription(
                    subscription,
                    subBtn,
                    function (response) {
                        if (response.status === 200) {
                            btnText = subBtn.querySelector(".btn-text");
                            btnText.textContent = btnText.textContent =
                                gettext("Turn off notifications");
                            subBtn.setAttribute("aria-pressed", true);
                            subBtn.disabled = false;
                            subBtn.isPushEnabled = true;
                        }
                    }
                );
            }
        });


        subBtn.addEventListener("click", function () {
            subBtn.disabled = true;
            if (subBtn.isPushEnabled) {
                return unsubscribe(registration, subBtn);
            }
            return subscribe(registration, subBtn);
        })
    }
})


function showMessage(message) {
    const messageBox = document.getElementById("webpush-message");

    if (messageBox) {
        messageBox.textContent = message;
        messageBox.hidden = false;
    }
}

function btnOff(btn, msg) {
    btn.disabled = false;
    btn.setAttribute("aria-pressed", false);
    btnText = btn.querySelector(".btn-text");
    btnText.textContent = btnText.textContent = gettext(
        "Turn on notifications"
    );
    showMessage(msg);
}

function subscribe(reg, subBtn) {
    reg.pushManager.getSubscription().then(async function (existingSub) {
        const metaObj = document.querySelector('meta[name="vapid-key"]');
        const applicationServerKey = metaObj.content;
        const options = { userVisibleOnly: true };
        if (applicationServerKey) {
            options.applicationServerKey = urlB64ToUint8Array(applicationServerKey);
        }

        try {
            const subscription = await reg.pushManager.subscribe(options);
            await postSubscribeObj("subscribe", subscription, subBtn, function (response) {
                if (response.status === 201) {
                    const btnText = subBtn.querySelector(".btn-text");
                    btnText.textContent = gettext("Turn off notifications");
                    subBtn.setAttribute("aria-pressed", "true");
                    subBtn.disabled = false;
                    subBtn.isPushEnabled = true;
                    showMessage(gettext("Successfully subscribed to push notifications."));
                }
            });
        } catch (err) {
            if (err.name === "InvalidStateError" && existingSub) {
                console.warn("Old subscription detected, unsubscribing...");
                await existingSub.unsubscribe();
                console.log("Old subscription removed, retrying subscribe...");
                subscribe(reg, subBtn);
            } else {
                console.error("Push subscription error:", err);
                showMessage(gettext("Error while subscribing to push notifications."));
                subBtn.disabled = false;
            }
        }
    });
}

function unsubscribe(reg, subBtn) {
    // Get the Subscription to unregister
    reg.pushManager.getSubscription().then(function (subscription) {
        // Check we have a subscription to unsubscribe
        if (!subscription) {
            // No subscription object, so set the state
            // to allow the user to subscribe to push
            let msg = gettext("Subscription is not available.");
            btnOff(subBtn, msg);
            return;
        }
        postSubscribeObj(
            "unsubscribe",
            subscription,
            subBtn,
            function (response) {
                // Check if the information is deleted from server
                if (response.status === 202) {
                    subscription
                        .unsubscribe()
                        .then(function (successful) {
                            btnOff(subBtn, gettext(
                                "Successfully unsubscribed from push notifications."
                            ));
                            subBtn.isPushEnabled = false;
                        })
                        .catch(function (error) {
                            showMessage(
                                gettext(
                                    "Error while unsubscribing from push notifications."
                                )
                            );
                            subBtn.disabled = false;
                        });
                } else {
                    btnOff(
                        subBtn,
                        gettext(
                            "Successfully unsubscribed from push notifications."
                        )
                    );
                    subBtn.isPushEnabled = false;
                }
            }
        );
    });
}

function checkSubscription(subscription, subBtn, callback) {
    const data = {
        subscription: subscription.toJSON(),
        // group: subBtn.dataset.group,
    };
    const headers = new Headers();
    const csrftoken = getCookie("csrftoken");
    headers.append("X-CSRFToken", csrftoken);
    headers.append("Content-Type", "application/json");

    fetch("/subscription-check/", {
        method: "post",
        mode: "same-origin",
        headers: headers,
        body: JSON.stringify(data),
    }).then(callback);
}

function postSubscribeObj(statusType, subscription, subBtn, callback) {
    const browser = navigator.userAgent
            .match(/(firefox|msie|chrome|safari|trident|opera|opr)/gi)[0]
            .toLowerCase(),
        user_agent = navigator.userAgent,
        data = {
            status_type: statusType,
            subscription: subscription.toJSON(),
            browser: browser,
            user_agent: user_agent,
            // group: subBtn.dataset.group,
        };
    const headers = new Headers();
    const csrftoken = getCookie("csrftoken");
    headers.append("X-CSRFToken", csrftoken);
    headers.append("Content-Type", "application/json");
    fetch(subBtn.dataset.url, {
        method: "post",
        mode: "same-origin",
        headers: headers,
        body: JSON.stringify(data),
    }).then(callback);
}

let deferredPrompt;
window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;

    const btnDiv = document.querySelector(".btn__wrapper");
    // wrapper only exists inside the settings modal markup
    if (!btnDiv || btnDiv.querySelector(".install-btn")) return;

    const installButton = document.createElement("button");
    installButton.type = "button";

    installButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-download" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/>
        <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708z"/>
    </svg><span>${gettext("Install App")}</span>`;
    installButton.classList.add("install-btn", "btn", "btn-secondary", "w-full", "gap-2");

    btnDiv.classList.add("mt-4", "border-t", "border-slate-200", "pt-4");

    installButton.addEventListener("click", async () => {
        if (deferredPrompt !== null) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === "accepted") {
                deferredPrompt = null;
            }
        }
        installButton.style.display = "none";
    });

    btnDiv.appendChild(installButton);
});
