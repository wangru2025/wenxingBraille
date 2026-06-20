# 文星点显器 NVDA 插件

这是文星 / CBP 40 方点显器的 NVDA 点显器驱动。

驱动直接通过 Windows WinUSB 与设备通信，不依赖阳光读屏的 `StarLibDriver.dll`。

## 功能

- 40 方盲文显示。
- 1 到 40 方光标路由键。
- 左右各三个功能键，映射到 NVDA 盲文导航命令。
- 使用设备接口 GUID `{58D07210-27C1-11DD-BD0B-0800200C9A66}` 直接通信。

## 按键映射

| 设备按键 | NVDA 命令 |
| --- | --- |
| 1 到 40 方路由键 | 路由到对应盲文方 |
| 左侧外键 | 上一盲文行 |
| 左侧中键 | 向后滚动盲文 |
| 左侧内键 | 跳到浏览顶部 |
| 右侧外键 | 下一盲文行 |
| 右侧中键 | 向前滚动盲文 |
| 右侧内键 | 跳到浏览底部 |

## 要求

- NVDA 2026.1.1 或更高版本。
- 文星 / CBP 点显器已安装 WinUSB 驱动。

## 构建

运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

生成的插件包位于 `dist\wenxingBraille-0.1.0.nvda-addon`。
