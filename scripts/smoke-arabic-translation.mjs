import { translateMarkdownToArabic } from "../server/reportTranslationService.ts";

const translated = await translateMarkdownToArabic("# Compatibility report\n\n> This is a symbolic calculation record, not a relationship verdict.\n\n| Score | 77% |");

if (!translated.includes('dir="rtl"')) throw new Error("Arabic translation was not wrapped for right-to-left rendering.");
if (!/[\u0600-\u06FF]/.test(translated)) throw new Error("Arabic translation did not contain Arabic text.");
if (!translated.includes("77%")) throw new Error("Arabic translation did not preserve the percentage.");

console.log("Arabic translation smoke test passed.");
