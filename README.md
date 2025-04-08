# astrbot_plugin_zanwo

[![GitHub](https://img.shields.io/badge/作者-Futureppo-blue)](https://github.com/Futureppo)


## 插件简介
**名片点赞插件**，用户发送指令 `赞我` 后，自动向用户发送最多 50 次名片赞。


# ⚠️ **需要配置！！需要配置！！请仔细阅读以下说明！！**


### 1. 确保 NapCat 的HTTP服务正常运行

插件依赖于 NapCat 的点赞接口，需满足以下条件：

- NapCat的HTTP服务已启动并运行在 `http://127.0.0.1:3000` 地址（默认配置）

- 若需修改端口或地址，请在代码中找到以下行并调整：
  ```python
  url = "http://127.0.0.1:3000/send_like"  # 根据实际情况修改
  ```


## 使用方法

### 触发指令
在聊天窗口发送以下指令即可触发点赞：
```text
赞我
```

## 注意事项

1. **点赞限制**  
   - 非好友每天只能点50人，每人50个。

2. **错误处理**  
   - 用户隐私设置未开启陌生人点赞权限时，直接提示失败。

---

## 联系作者
- **GitHub**：[Futureppo 的 GitHub](https://github.com/Futureppo)
- **反馈**：欢迎在 [GitHub Issues](https://github.com/Futureppo/astrbot_plugin_zanwo/issues) 提交问题或建议

---