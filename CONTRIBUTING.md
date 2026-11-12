# Contributing

- Keep this project standalone; integrations must be optional.
- Never read, print, copy, or store API credentials.
- Never use the paid-enabled diagnostic key.
- Never perform model inference as part of import, list, summary, or export commands.
- Preserve raw provider-reported token counts without converting them into assumed Pollen charges.
- Keep requested model IDs and actual routed IDs separate.
- Do not mark a model Quest-compatible unless the test used the Quest-only restricted key.
- Do not equate HTTP 200 with a quality pass.
- Avoid overwrites and automatic Git commits.
