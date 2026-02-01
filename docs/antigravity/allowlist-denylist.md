# 白名单 / 黑名单 (Allowlist / Denylist)
浏览器使用双层安全系统来控制可以访问的 URL：

* **黑名单 (Denylist)**：拒绝危险/恶意 URL
* **白名单 (Allowlist)**：显式允许受信任的 URL

## 工作原理

### 黑名单 (Denylist)
黑名单由 Google Superroots 的 BadUrlsChecker 服务维护和强制执行。当浏览器尝试导航至某个 URL 时，会通过 RPC 检查主机名是否在服务器端黑名单中。

**注意**：如果服务器不可用，默认情况下将拒绝访问。

### 白名单 (Allowlist)
白名单是一个本地文本文件，您可以对其进行编辑以显式信任特定的 URL。
