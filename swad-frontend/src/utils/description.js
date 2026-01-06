export function summarizeComboDescription(raw = "") {
  if (!raw) return "";
  // Normalize separators
  const parts = raw
    .split(/\r?\n|•|,|;/)
    .map((p) => p.trim())
    .filter(Boolean);

  function humanizeToken(token) {
    const t = token.toLowerCase();

    // 10 Idli -> 10 Soft Idlis
    const idliMatch = t.match(/^(\d+)\s*idli/);
    if (idliMatch) {
      const n = Number(idliMatch[1]);
      return `${n} Soft Idli${n > 1 ? "s" : ""}`;
    }

    // Sambar 400ml -> Hot Sambar (2 bowls)
    const sambarMatch = t.match(/sambar\s*(?:-|:)?\s*(\d+)\s*ml/);
    if (sambarMatch) {
      const ml = Number(sambarMatch[1]);
      const bowls = Math.max(1, Math.round(ml / 200));
      return `Hot Sambar (${bowls} bowl${bowls > 1 ? "s" : ""})`;
    }
    if (t.includes("sambar")) {
      return `Hot Sambar`;
    }

    // Chutney -> Fresh Coconut Chutney when coconut present
    if (t.includes("coconut") || t.includes("chutney")) {
      if (t.includes("coconut")) return `Fresh Coconut Chutney`;
      return `Fresh Chutney`;
    }

    // Default: capitalize first letter and drop technical units like ml
    const cleaned = token.replace(/\b(\d+)\s*ml\b/gi, "").trim();
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  }

  const humanParts = parts.map(humanizeToken).slice(0, 3);
  return humanParts.join(" • ");
}
