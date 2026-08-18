import { invokeLLM } from "./_core/llm";

export async function translateMarkdownToArabic(markdown: string) {
  const response = await invokeLLM({
    model: "gpt-5-mini",
    maxTokens: 16000,
    messages: [
      {
        role: "system",
        content: "You are a precise professional English-to-Arabic report translator. Return Markdown only. Preserve all headings, tables, HTML div tags, links, dates, percentages, names, calculation labels, numbers, technical system names, and symbolic outputs exactly unless they have a standard Arabic equivalent. Translate only user-facing explanatory prose. Do not add interpretation, scores, claims, or advice. Keep Markdown pipe-table structure valid. Use Modern Standard Arabic and direct, gender-neutral phrasing where possible.",
      },
      { role: "user", content: markdown },
    ],
  });
  const content = response.choices[0]?.message.content;
  if (typeof content !== "string" || !content.trim()) throw new Error("Arabic translation returned no report content.");
  return `<div dir="rtl" class="arabic-report">\n\n${content.trim()}\n\n</div>`;
}
