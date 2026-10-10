const leadForm = document.querySelector("[data-lead-form]");

if (leadForm) {
    let formStartTracked = false;
    leadForm.addEventListener("focusin", () => {
        if (!formStartTracked && window.umami?.track) {
            window.umami.track("lead-form-started");
            formStartTracked = true;
        }
    });
}

if (document.querySelector("[data-lead-submitted]") && window.umami?.track) {
    window.umami.track("lead-submitted");
}
