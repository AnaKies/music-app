import { renderCaseEntryScreen } from "../features/cases/case-entry-screen.js";

const rootElement = document.querySelector("#app");

if (!rootElement) {
  throw new Error("Expected #app root element.");
}

renderCaseEntryScreen(rootElement);
