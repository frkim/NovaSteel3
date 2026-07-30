// Post-processes a Marp-generated .pptx so every speaker note renders as one
// paragraph per authored line instead of a single wall of text.
//
// Marp preserves the newlines we author inside the note run, but PowerPoint
// ignores raw line feeds inside <a:t>: readable line breaks require one <a:p>
// paragraph per line. This rewrites each ppt/notesSlides/notesSlideN.xml part.
//
// Usage: node scripts/format-pptx-notes.mjs dist/NovaSteel-Oral-Defense.pptx

import AdmZip from "adm-zip";

const file = process.argv[2] || "dist/NovaSteel-Oral-Defense.pptx";

const notePartPattern = /ppt\/notesSlides\/notesSlide\d+\.xml$/;
const noteParagraphPattern =
  /<a:p><a:r><a:rPr lang="en-US" dirty="0"\/><a:t>([\s\S]*?)<\/a:t><\/a:r><a:endParaRPr lang="en-US" dirty="0"\/><\/a:p>/;

const zip = new AdmZip(file);
let rewritten = 0;

for (const entry of zip.getEntries()) {
  if (!notePartPattern.test(entry.entryName)) continue;

  const xml = zip.readAsText(entry);
  const match = xml.match(noteParagraphPattern);
  if (!match) continue;

  const lines = match[1]
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length < 2) continue;

  const paragraphs = lines
    .map(
      (line) =>
        `<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>${line}</a:t></a:r><a:endParaRPr lang="en-US" dirty="0"/></a:p>`,
    )
    .join("");

  zip.updateFile(entry, Buffer.from(xml.replace(noteParagraphPattern, paragraphs), "utf8"));
  rewritten += 1;
}

zip.writeZip(file);
console.log(`format-pptx-notes: split speaker notes into paragraphs on ${rewritten} slides`);
