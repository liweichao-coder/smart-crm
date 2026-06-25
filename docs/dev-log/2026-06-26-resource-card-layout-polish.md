# 2026-06-26 Resource Card Layout Polish

## 背景

- 验收资源页时发现卡片层级不够清楚，搜索、字段显示、偏好状态混在同一个横向区域，中等宽度下容易显得拥挤。
- 浏览器中宽视口复验时，发现 `.crm-toolbar-card` 被通用 `justify-content: space-between` 覆盖，导致内部内容没有铺满卡片。

## 本次调整

- 将 `ResourceToolbar` 拆成搜索/状态行与字段显示行，职责更清晰。
- 给工具栏自身增加 container query，按工具栏实际宽度决定搜索行是否拆行。
- 将字段显示从 flex 换成 `auto-fit` 网格，避免列选择项在中宽页面堆挤。
- 移除工具栏与通用 `space-between` 规则的冲突，使工具卡片内容铺满。
- 修复通知铃角标造成的细小横向溢出。

## 验收记录

- 在 1059 x 736 视口检查 `/dashboard`、`/accounts`、`/orders`、`/copilot`、`/reports`。
- `/accounts` 工具栏高度从 298px 降到 209px，字段显示为 6 列两行，无横向溢出。
- 关键页面未发现浏览器控制台 error。

