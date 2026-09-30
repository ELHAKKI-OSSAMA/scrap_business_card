import type { TFunction } from "i18next";

/** Extraction notes come from the API as stable English strings; known ones are translated here,
 * unknown ones are shown verbatim (never dropped). */
const PATTERNS: [RegExp, (m: RegExpMatchArray, t: TFunction) => string][] = [
  [/^honorific: (.+)$/, (m, t) => t("notes.honorific", { v: m[1] })],
  [/^matched: (.+)$/, (m, t) => t("notes.matched", { v: m[1] })],
  [/^inferred from job-title keywords$/, (_m, t) => t("notes.inferred_title")],
  [/^inferred from '(.+)'$/, (m, t) => t("notes.inferred_from", { v: m[1] })],
  [/^split rule: (.+)$/, (m, t) => t("notes.split", { v: m[1] })],
  [/^No verified handwriting recognizer/, (_m, t) => t("notes.no_hw")],
  [/^company marker$/, (_m, t) => t("notes.company_marker")],
  [/^matches e-mail\/website domain$/, (_m, t) => t("notes.domain_match")],
  [/^academic\/medical title printed before the name$/, (_m, t) => t("notes.academic")],
  [/^suggested by language model/, (_m, t) => t("notes.llm")],
  [/^explicit specialty term printed on the card$/, (_m, t) => t("notes.explicit_specialty")],
  [/^verbatim professional scope$/, (_m, t) => t("notes.verbatim_scope")],
  [/^inferred: honorific '(.+)' \+ printed medical specialty/, (m, t) => t("notes.inferred_doctor", { v: m[1] })],
  [/^inferred from medical specialty$/, (_m, t) => t("notes.inferred_medical")],
  [/^possible_fragment_of:(.+)$/, (m, t) => t("notes.possible_fragment", { v: m[1] })],
  [/^bare_domain$/, (_m, t) => t("notes.bare_domain")],
];

export function translateNote(note: string | null | undefined, t: TFunction): string | null {
  if (!note) return null;
  for (const [rx, fn] of PATTERNS) {
    const m = note.match(rx);
    if (m) return fn(m, t);
  }
  return note;
}
