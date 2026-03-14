"use client";
import { Lang, LANGUAGE_OPTIONS } from "./translations";

export function LanguageSelector({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
    return (
        <select
            value={lang}
            onChange={(e) => setLang(e.target.value as Lang)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-400 cursor-pointer"
        >
            {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.code} value={opt.code}>
                    {opt.nativeLabel}
                </option>
            ))}
        </select>
    );
}
