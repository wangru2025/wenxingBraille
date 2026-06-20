# Wenxing Braille Display NVDA Add-on

This add-on provides an NVDA braille display driver for the Wenxing / CBP 40-cell braille display.

The driver talks to the device directly through Windows WinUSB and does not depend on Sunshine Screen Reader's `StarLibDriver.dll`.

## Features

- 40-cell braille output.
- Cursor routing keys for cells 1 through 40.
- Six side keys mapped to NVDA braille navigation commands.
- Direct WinUSB communication with device interface `{58D07210-27C1-11DD-BD0B-0800200C9A66}`.

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
- Windows WinUSB driver for the Wenxing / CBP braille display.

## Build

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The add-on package will be written to `dist\wenxingBraille-0.1.0.nvda-addon`.

## Chinese README

See [README.zh_CN.md](README.zh_CN.md).
