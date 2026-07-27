# 02 — AxelorMetal corporate website

**Audience:** complete newcomers to steel and NovaSteel  
**Reading time:** 16 minutes  
**Persona:** public visitor / jury member / all personas  
**Routes covered:** `/{site}/company-website/home`, `/{site}/company-website/company`, `/{site}/company-website/products`, `/{site}/company-website/steel-knowledge`, `/{site}/company-website/contact`  
**Last updated:** 2026-07-27  
[🇫🇷 Version française](../fr/02-company-website.md)

## Why a fictitious website is in the defense

AxelorMetal is the fictitious Luxembourg steel producer. NovaSteel is the AI-powered decision-support platform it operates. The website exists so a non-steel audience first understands the operator, its plants, products, and regulatory world before seeing operational dashboards. The demo runbook explicitly says to “open with the AxelorMetal public website to establish the fictitious company narrative before entering the NovaSteel platform” (`docs\demo\demo-runbook.md:3-6`).

The UX spec defines this section as “a fictitious corporate website, not an operational cockpit” (`docs\ux\dashboard-specification.md:901-904`). All five sub-views are registered in routing metadata and the screen registry (`apps\analytics-mfe\src\personaRoutes.ts:167-180`; `apps\analytics-mfe\src\components\screens\screenRegistry.ts:59-63`). The site is localized in EN/FR/DE/NL/ES and each article is rendered as one full-bleed, non-closable dock panel (`docs\ux\dashboard-specification.md:915-919`; `apps\analytics-mfe\src\components\screens\CompanyWebsiteLayout.tsx:21-39`).

---

## Home — `/{site}/company-website/home`
![AxelorMetal website home page](../screenshots/company-website-home.png)

**In one sentence.** The Home page introduces AxelorMetal as the steel operator and NovaSteel as the AI platform behind cleaner, safer, more efficient steelmaking.

**Steel-industry background (for newcomers).** Steelmaking turns iron ore or recycled scrap into steel, then shapes it into products. An “integrated producer” controls multiple steps: ironmaking, steelmaking, rolling, and finishing. Rolling means squeezing steel through large rollers to make sheets, coils, plates, rails, bars, or beams (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:30-63`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:141-173`).

**What you see on screen.**

1. **NovaSteel shell.** The top bar shows site, persona, search, Fabric status, demo badge, theme, and language; the left navigation highlights AxelorMetal under Platform & Reference (`docs\ux\dashboard-specification.md:172-175`; `apps\analytics-mfe\src\personaRoutes.ts:167-180`).
2. **Synthetic-data banner.** The purple banner says “Synthetic demo data — not for operational control,” matching the runbook’s requirement that every tab clearly labels demo data (`docs\demo\demo-runbook.md:37-44`).
3. **Website tabs.** Home, Company, Products & Markets, Steel Knowledge, and Contact are the five routed sub-views (`apps\analytics-mfe\src\personaRoutes.ts:173-180`; `docs\ux\dashboard-specification.md:905-913`).
4. **Dark hero panel.** “Engineering the future of steel” sits on a dark blue gradient with buttons “Discover AxelorMetal” and “Explore our products” (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:81-139`).
5. **Who-we-are cards.** Four visible cards explain integrated production, AI-driven optimization, responsible steelmaking, and steel knowledge. Blue icons mark production/AI, green marks sustainability, and purple marks learning (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:30-55`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:141-173`).
6. **Lower profile table.** Below the first fold, “AxelorMetal at a glance” lists headquarters, operating region, industry, production routes, and regulatory context (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:57-63`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:175-198`).

**Why this component was implemented.** It turns the use-case line “A Luxembourg-based integrated steel producer operating blast furnaces and rolling mills across four countries faces…” into a memorable business story (`docs\usecase\usecase.md:14-22`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Business identity and footprint | CHL-01..CHL-05 context | Home states the four-country steel producer story. | No screen API; static content in `CompanyWebsiteHome.tsx` (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:146-150`). |
| Transformation objective | OBJ-01..OBJ-04 | “AI-driven optimization” mentions wear prediction, energy optimization, and operator expertise. | No screen API; static card content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:38-41`). Proof IDs are cataloged in `apps\analytics-mfe\src\proof\proofCatalog.ts:337-410`. |
| Regulatory framing | REG-01..REG-03 | The lower page names GDPR, EU AI Act, and sector directives. | No screen API; static alert/table content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:219-223`). |

**How the data reaches this screen.** `CompanyWebsiteHome` renders static React content and translated labels from `useAnalytics`; it does not call `DataClient` or a BFF route (`apps\analytics-mfe\src\components\screens\CompanyWebsiteHome.tsx:72-80`; `apps\analytics-mfe\src\api\dataClient.ts:151-322`).

**Honesty & caveats.** AxelorMetal, its logo, people, plants, and contact story are fictional; this page is narrative context, not real corporate evidence (`docs\ux\dashboard-specification.md:901-904`).

**Try it yourself.** Open `http://localhost:5266/lu/company-website/home`, click **Discover AxelorMetal**, then return to the Home tab.

---

## Company — `/{site}/company-website/company`
![AxelorMetal company page](../screenshots/company-website-company.png)

**In one sentence.** The Company page explains AxelorMetal’s mission, operating footprint, production routes, sustainability posture, and compliance story.

**Steel-industry background (for newcomers).** A blast furnace uses iron ore, coke, and limestone to make molten iron. A basic oxygen furnace, or BOF, turns molten iron into steel by blowing oxygen through it. An electric arc furnace, or EAF, melts scrap steel using electric arcs. AxelorMetal is shown as operating both major routes (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:203-219`).

**What you see on screen.**

1. **Hero band.** “About AxelorMetal” describes a Luxembourg-based integrated steel producer using AI to make steel cleaner, safer, and more efficient (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:68-89`).
2. **About accordion.** The expanded panel contains mission, vision, company profile, story, NovaSteel difference, and measurable-impact cards (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:91-189`).
3. **Company profile table.** Rows list heavy industry & metals, Luxembourg headquarters, four-country region, BF/BOF and EAF routes, and regulatory context (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:118-136`).
4. **AI infusion bullets.** Check-mark bullets name lining prediction, energy dispatch optimization, and GenAI knowledge capture, matching the use case’s AI infusion points (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:147-165`; `docs\usecase\usecase.md:46-50`).
5. **Impact cards.** Cards show −14% energy, −22% CO₂, +8% high-grade yield, and 21 days warning. These are targets, not measured production results (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:167-182`; `docs\presentation\proof_of_execution.md:307-315`).
6. **Lower accordions.** “Our Activities,” “Sustainability,” and “Compliance” explain BF/BOF, EAF, rolling, GDPR, EU AI Act, ETS, CBAM, and worker-safety context (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:191-557`).

**Why this component was implemented.** It makes the transformation objective visible: “Implement an **AI-driven production optimization platform** that” reduces energy, predicts equipment failures, improves quality, and captures expertise (`docs\usecase\usecase.md:26-33`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| AI infusion strategy | AI-01, AI-02, AI-03 | The “AxelorMetal difference” bullets name all three AI patterns. | No screen API; static content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:147-165`). Proof catalog: `apps\analytics-mfe\src\proof\proofCatalog.ts:520-608`. |
| Expected outcomes | OUT-01..OUT-04 | Four blue impact cards show −14%, −22%, +8%, and 21 days. | No screen API; static target cards (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:167-182`). Caveat: `docs\presentation\proof_of_execution.md:307-315`. |
| Regulatory context | REG-01..REG-03 | Profile and Compliance accordion cite GDPR, EU AI Act, ETS, IED, CBAM, and OSH. | No screen API; static content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:123-128`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:370-546`). |

**How the data reaches this screen.** `CompanyWebsiteCompany` is static React content; navigation uses `emit('nav.intent')` and no BFF data route is called (`apps\analytics-mfe\src\components\screens\CompanyWebsiteCompany.tsx:59-67`).

**Honesty & caveats.** The impact numbers are synthetic-demo targets. The proof document says the mechanisms run, but the magnitudes are generated data properties (`docs\presentation\proof_of_execution.md:307-315`).

**Try it yourself.** Open `http://localhost:5266/lu/company-website/company`, expand **Sustainability**, then expand **Compliance**.

---

## Products & Markets — `/{site}/company-website/products`
![AxelorMetal products page](../screenshots/company-website-products.png)

**In one sentence.** The Products page explains what kinds of steel AxelorMetal sells and why product shape, grade, surface, chemistry, and customer market matter.

**Steel-industry background (for newcomers).** Flat products are wide, thin products such as sheets, plates, coils, and strips. Long products are beams, rails, bars, rods, and wire rod. A steel grade is a specification for chemistry and mechanical properties. HSLA means high-strength low-alloy steel, used when lighter but stronger structures are needed (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:23-40`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:117-151`).

**What you see on screen.**

1. **Hero band.** “Products” appears with a sentence about mechanical, chemical, and dimensional requirements (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:72-95`).
2. **Flat product cards.** Hot-rolled coils & sheets, cold-rolled coils & sheets, heavy plate, and coated & galvanized steel are shown as cards. Good fit means the product matches the customer application; bad fit means the surface, thickness, strength, or corrosion protection is wrong (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:23-40`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:97-115`).
3. **Long products list.** Beams, rails, bars, rods, and wire rod are listed for construction, railways, machining, reinforcement, manufacturing, cable, and fasteners (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:117-133`).
4. **Grades and specialty steels.** Carbon steel, HSLA, stainless steel, and custom alloy steel explain why “steel” is a family, not one material (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:135-152`).
5. **Blue information alert.** The alert links to “Metal Families” on Steel Knowledge for readers who need metallurgy basics (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:154-160`).
6. **Markets below the fold.** Automotive, construction & infrastructure, energy, and industrial manufacturing are described lower on the page (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:179-263`).

**Why this component was implemented.** It connects the challenge “Quality consistency issues in high-grade steel for automotive customers” to visible product families and markets (`docs\usecase\usecase.md:20-22`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Quality challenge | CHL-04 | Product and market content explains why automotive-grade consistency matters. | No screen API; static content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:135-160`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:187-237`). |
| Improve steel quality | OBJ-03, OUT-04 | The page frames the business reason for high-grade yield, but does not calculate yield. | No screen API; OUT-04 proof is cataloged under Quality (`apps\analytics-mfe\src\proof\proofCatalog.ts:495-518`). |
| Knowledge handoff | CHL-05 context | The page sends beginners to Metal Families. | No screen API; navigation via `navigate('steel-knowledge')` (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:154-160`). |

**How the data reaches this screen.** Product and market arrays are embedded in `CompanyWebsiteProducts`; no `DataClient` or BFF route is used (`apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:23-69`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteProducts.tsx:72-268`).

**Honesty & caveats.** The catalog is illustrative. It teaches plausible categories, not a real sales catalog (`docs\ux\dashboard-specification.md:901-904`).

**Try it yourself.** Open `http://localhost:5266/lu/company-website/products`, read **Grades and specialty steels**, then click the **Metal Families** link.

---

## Steel Knowledge — `/{site}/company-website/steel-knowledge`
![AxelorMetal steel knowledge page](../screenshots/company-website-steel-knowledge.png)

**In one sentence.** Steel Knowledge is the best beginner on-ramp because it teaches metal families, steelmaking routes, shaping methods, process diagrams, and a searchable glossary.

**Steel-industry background (for newcomers).** Iron is a chemical element. Steel is an alloy: mostly iron with a small amount of carbon. Cast iron has more carbon than steel, making it hard but brittle. Stainless steel contains chromium, which helps resist rust. Non-ferrous metals are not mainly iron-based, such as aluminum, copper, zinc, and titanium (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:169-258`).

**What you see on screen.**

1. **Hero band.** “Steel, iron, and other metals” introduces plain-language metallurgy (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:113-136`).
2. **Beginner alert.** A blue note tells new readers to begin with **Metal Families** and follow the sections in order (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:138-149`).
3. **Six learning cards.** Metal Families, Making Iron & Steel, Producing Other Metals, Shaping Metals, Key Takeaways, and Glossary scroll to their sections (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:60-99`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:151-167`).
4. **Open Metal Families accordion.** It explains iron, steel, cast iron, stainless steel, alloy steels, and non-ferrous metals. Good understanding: steel is a material family; bad understanding: all iron-based materials behave alike (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:169-258`).
5. **Comparison table.** A table compares iron-based materials by composition and key characteristic (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:212-238`).
6. **CompanyWebsiteDiagram / ProcessDiagram.** Lower sections include three zoomable diagrams: integrated BF/BOF route, EAF route, and detailed EAF process. Clicking an image opens a lightbox with zoom from 100% to 400% (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:261-360`; `apps\analytics-mfe\src\components\screens\CompanyWebsiteDiagram.tsx:32-168`).
7. **Glossary DataTable.** The glossary has term and definition columns plus global search, per-column search, sort, column chooser, density toggle, export, and pagination (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:533-550`; `apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-428`).

**Why this component was implemented.** The use case says “Skilled operators [are] retiring, with knowledge disappearing faster than it can be captured” (`docs\usecase\usecase.md:20-22`). This page is not the GenAI capture system, but it uses the same principle: make industrial knowledge explicit.

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Beginner knowledge transfer | CHL-05, OBJ-04 | Plain-language lessons and searchable glossary. | No screen API; static glossary and content (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:42-58`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:169-550`). |
| Process context for AI | AI-01, AI-02 | Diagrams show equipment later monitored by Furnace Health and Energy Optimization. | No screen API; `/media/*.webp` images rendered by `ProcessDiagram` (`apps\analytics-mfe\src\components\screens\CompanyWebsiteDiagram.tsx:20-40`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:273-333`). |
| Website acceptance | S-24 / AC-S24-3 | Glossary supports table search. | No screen API; `DataTable` implementation (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:533-550`; `apps\analytics-mfe\src\components\primitives\DataTable.tsx:248-428`). |

**How the data reaches this screen.** The page uses static arrays for glossary rows and overview cards, then renders `/media` images through `ProcessDiagram`; there is no BFF or fixture-worker call (`apps\analytics-mfe\src\components\screens\CompanyWebsiteSteelKnowledge.tsx:42-107`; `apps\analytics-mfe\src\components\screens\CompanyWebsiteDiagram.tsx:77-87`).

**Honesty & caveats.** The lesson is simplified for a demo audience. It is not a metallurgical textbook or an operating procedure (`docs\demo\demo-runbook.md:106-121`).

**Try it yourself.** Open `http://localhost:5266/lu/company-website/steel-knowledge`, click **Making Iron & Steel**, then click a process diagram and try the zoom controls.

---

## Contact — `/{site}/company-website/contact`
![AxelorMetal contact page](../screenshots/company-website-contact.png)

**In one sentence.** Contact completes the fiction by showing how customers, partners, sustainability stakeholders, and candidates would approach AxelorMetal.

**Steel-industry background (for newcomers).** A steel producer is part of a supply chain. Customers ask about products and grades; partners discuss innovation or sustainability; regulators and communities care about climate and privacy; future employees care about careers and safety. The page turns those groups into simple cards (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:24-53`).

**What you see on screen.**

1. **Hero band.** “Contact AxelorMetal” invites customers, partners, future colleagues, and curious visitors (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:71-92`).
2. **Head office card.** The card states “AxelorMetal S.A., Luxembourg, European Union” (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:94-101`).
3. **Get-in-touch cards.** Sales & products, Partnerships, Sustainability, and Careers appear as cards; blue icons mark commercial/partner paths, green marks sustainability, and orange marks careers (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:24-53`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:103-127`).
4. **Where we operate.** Luxembourg, Germany, Belgium, and Spain are listed, with Luxembourg marked as headquarters (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:55-60`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:129-155`).
5. **Privacy note below the fold.** A GDPR privacy alert explains responsible personal-data handling and links to the Company page (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:157-170`).

**Why this component was implemented.** It reinforces the industry profile: “Headquarters: Luxembourg” and “Operating Region: Luxembourg, Germany, Belgium, Spain” (`docs\usecase\usecase.md:5-10`).

**Objective & evidence (proof of execution).**

| Use-case element | Requirement ID | Evidence in the running app | Where the number comes from (API route + source file) |
|---|---|---|---|
| Operating footprint | CHL-01..CHL-05 context | The four operating countries are visible. | No screen API; `LOCATIONS` array (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:55-60`). |
| GDPR awareness | REG-01 | The privacy alert explains GDPR handling. | No screen API; static alert (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:157-170`). |
| Stakeholder navigation | OBJ-01..OBJ-04 context | Cards navigate to products, company, and sustainability context. | No screen API; route intent code (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:62-67`, `apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:103-127`). |

**How the data reaches this screen.** `CompanyWebsiteContact` renders constants for cards and locations; it does not call `DataClient` or BFF routes (`apps\analytics-mfe\src\components\screens\CompanyWebsiteContact.tsx:24-67`; `apps\analytics-mfe\src\api\dataClient.ts:151-322`).

**Honesty & caveats.** There is no real lead form, email submission, or corporate contact workflow. This is a demo narrative artifact (`docs\ux\dashboard-specification.md:901-919`).

**Try it yourself.** Open `http://localhost:5266/lu/company-website/contact`, click **Explore our products**, then return to Contact.

---

[◀ Previous: Shell and navigation](01-shell-and-navigation.md) · [▲ Index](README.md) · [Next ▶ Command Center and Operations](03-command-center-and-operations.md)
