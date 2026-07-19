# Browser companion

Shared local extension architecture for ChatGPT Web, Gemini Web, and Grok Web.

The companion will contain site-specific observers but one transport, consent model, deduplication layer, and local Mneme service client. It is required because none of the three web products currently exposes a verified native post-turn lifecycle hook that can guarantee an external ledger write.

Status: design-ready; implementation starts after the semantic extractor contract is ratified.
