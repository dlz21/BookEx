import "./prototype.css";

// Progressive enhancement only: Django renders the errors and owns validation.
// Native forms continue to submit when JavaScript is unavailable.
document.querySelector<HTMLElement>("[data-form-errors]")?.focus();
