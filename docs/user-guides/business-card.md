# Business Card Intelligence — user guide

Web: `http://<server>/cards/` · Mobile: **Business cards** tab of the OCR Scanner app.
Interface languages: English, Français, العربية (right-to-left).

## 1. Add cards

* **New** → add the front (required) and back (optional, e.g. the Arabic side), then **Process**.
* **Batch upload** (web): select many images; each becomes a card and is processed in turn.
* Mobile: **Scan document** (automatic crop), camera or gallery; works offline as drafts.

## 2. Review

Fields: full name, first/last name, Arabic name, job title, company, department, industry,
phones (typed mobile / phone / fax / WhatsApp, normalised to international format), emails, website,
LinkedIn and other profiles, address, qualifications, QR codes.

* Each value shows its **confidence**, its source lines on the image, and **Needs review** when
  uncertain.
* Phone numbers without an international prefix are interpreted using **Settings → Default phone
  country** (e.g. MA, FR). Leave it empty to avoid guessing.
* Emails are validated; an invalid correction is refused with a message.
* Click the target icon on a field to highlight its source text on the image. Each field shows the
  OCR text it came from, the normalized value (when different), the source region, the confidence
  and its review status.
* **Specialty** is filled only when a specialty is printed (e.g. "Hépato-gastroentérologie");
  a description such as "Spécialiste des maladies du foie…" is kept verbatim under
  **Professional description** and never converted into a specialty.
* A title that is not printed (e.g. "Médecin" deduced from "Dr" + a medical specialty) is marked
  *inferred*, has a low confidence, always needs review and is not exported until you confirm it.
* Numbers without an international prefix are normalized only with a default phone country or a
  country printed in the card's own address (then marked for review) — never from the language.
* **QR codes** are decoded and the link is shown with a safety check, but it is **never opened
  automatically** — open it yourself only if you trust it. A comparison table shows each QR value
  next to what was read on the card (same / different / only in QR). Nothing is copied from the
  QR code unless you click **Import into contact**, and import never overwrites existing values.

## 3. Correct

Edit, add or remove values (e.g. a second phone), or **Confirm** correct ones. History keeps every
change; the raw OCR text is never altered.

## 4. Duplicates

**Possible duplicates** lists cards sharing an email, a phone number, or the same name and
company. Nothing is merged automatically: open the suggestion, compare, and choose **Merge** to
combine them (recorded in history).

## 5. Export

One card or all results as **vCard (.vcf)** — only values read from the card or confirmed by you — for phones and address books, **CSV** (Excel-safe,
Arabic preserved, protected against formula injection) or **JSON**.

## Limitations

* Tested only on synthetic printed cards (see `docs/models/evaluation.md`): names and titles
  ~98–99 % exact, companies ~92 %, postal codes on Arabic lines ~85 %.
* Stylised logos, very small text, glossy reflections and vertical text were not evaluated.
* Phone/e-mail icons are not recognised as symbols; phone types come from printed labels
  ("Tél", "Mob", "Fax", "الهاتف" …).
* An Arabic line that repeats the company or clinic name (e.g. "عيادة أمراض الكبد والجهاز الهضمي")
  stays in the OCR text; only one company value is stored.
* No real photographed cards have been evaluated yet.
* Handwritten notes on cards are not supported as a verified feature.
* No automatic translation of names or titles.
