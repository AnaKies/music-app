function createSection(title, description, content) {
  const section = document.createElement("section");
  section.className = "case-entry-section";

  const heading = document.createElement("h2");
  heading.className = "case-entry-section__title";
  heading.textContent = title;

  const text = document.createElement("p");
  text.className = "case-entry-section__description";
  text.textContent = description;

  section.append(heading, text, content);
  return section;
}

function createSuggestedCaseCard() {
  const card = document.createElement("article");
  card.className = "case-card case-card--suggested";

  const badge = document.createElement("span");
  badge.className = "case-card__badge";
  badge.textContent = "Suggested case";

  const title = document.createElement("h3");
  title.className = "case-card__title";
  title.textContent = "No recommended case yet";

  const text = document.createElement("p");
  text.className = "case-card__text";
  text.textContent =
    "This area will later highlight the most recently used active case.";

  card.append(badge, title, text);
  return card;
}

function createOtherCasesPlaceholder() {
  const list = document.createElement("div");
  list.className = "case-list";

  const placeholder = document.createElement("article");
  placeholder.className = "case-card case-card--placeholder";

  const title = document.createElement("h3");
  title.className = "case-card__title";
  title.textContent = "Other cases will appear here";

  const text = document.createElement("p");
  text.className = "case-card__text";
  text.textContent =
    "The list scaffold is ready for future backend-backed case summaries.";

  placeholder.append(title, text);
  list.append(placeholder);

  return list;
}

function createNewCaseAction() {
  const container = document.createElement("div");
  container.className = "new-case-action";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "new-case-action__button";
  button.textContent = "Start New Case";

  const text = document.createElement("p");
  text.className = "new-case-action__text";
  text.textContent =
    "This button is a scaffold for the future case-creation flow.";

  container.append(button, text);
  return container;
}

export function renderCaseEntryScreen(rootElement) {
  const page = document.createElement("main");
  page.className = "case-entry-page";

  const hero = document.createElement("header");
  hero.className = "case-entry-hero";

  const eyebrow = document.createElement("p");
  eyebrow.className = "case-entry-hero__eyebrow";
  eyebrow.textContent = "F1 · Case Entry";

  const title = document.createElement("h1");
  title.className = "case-entry-hero__title";
  title.textContent = "Choose a case or start a new transposition flow.";

  const description = document.createElement("p");
  description.className = "case-entry-hero__description";
  description.textContent =
    "This first scaffold separates the recommended case area, the reusable case list, and the new-case entry path.";

  hero.append(eyebrow, title, description);

  const content = document.createElement("div");
  content.className = "case-entry-layout";

  content.append(
    createSection(
      "Suggested case",
      "Reserved for the default active case that should be emphasized first.",
      createSuggestedCaseCard(),
    ),
    createSection(
      "Other cases",
      "Reserved for the full list of reusable transposition cases.",
      createOtherCasesPlaceholder(),
    ),
    createSection(
      "Create new case",
      "Reserved for entering the new-case flow when no existing case should be reused.",
      createNewCaseAction(),
    ),
  );

  page.append(hero, content);
  rootElement.replaceChildren(page);
}
