# Wenxing Braille Display NVDA Add-on

This add-on provides an NVDA braille display driver for the Wenxing / CBP 40-cell braille display.

## Features

- 40-cell braille output.
- Cursor routing keys for cells 1 through 40.
- Six side keys mapped to NVDA braille navigation commands.

## Key Mapping

| Device key | NVDA command |
| --- | --- |
| Routing keys 1-40 | Route to braille cell |
| Left outer | Previous braille line |
| Left middle | Scroll braille back |
| Left inner | Review top |
| Right outer | Next braille line |
| Right middle | Scroll braille forward |
| Right inner | Review bottom |

## Requirements

- NVDA 2026.1.1 or later.

## Build

Run:

```powershell
.\build.ps1
```

The add-on package will be written to `dist\wenxingBraille-1.0.0.nvda-addon`.
