import "./prototype.css";
import "./shell.css";
import "./book-list.css";

const navigationToggle = document.querySelector<HTMLButtonElement>("#navigation-toggle");
const navigation = document.querySelector<HTMLElement>("#primary-navigation");

if (navigationToggle && navigation) {
  const narrowScreen = window.matchMedia("(max-width: 48rem)");
  const setExpanded = (expanded: boolean) => {
    navigationToggle.setAttribute("aria-expanded", String(expanded));
    navigation.hidden = !expanded;
  };
  const updateLayout = () => {
    // Move focus before hiding a control or a navigation link on resize.
    if (narrowScreen.matches) {
      navigationToggle.hidden = false;
      if (navigation.contains(document.activeElement)) navigationToggle.focus();
      setExpanded(false);
    } else {
      setExpanded(true);
      if (document.activeElement === navigationToggle) {
        navigation.querySelector<HTMLAnchorElement>("a")?.focus();
      }
      navigationToggle.hidden = true;
    }
  };
  navigationToggle.addEventListener("click", () => {
    setExpanded(navigationToggle.getAttribute("aria-expanded") !== "true");
  });
  navigation.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && narrowScreen.matches) {
      navigationToggle.focus();
      setExpanded(false);
    }
  });
  narrowScreen.addEventListener("change", updateLayout);
  updateLayout();
}

// Progressive enhancement only: Django renders the errors and owns validation.
// Native forms continue to submit when JavaScript is unavailable.
document.querySelector<HTMLElement>("[data-form-errors]")?.focus();
