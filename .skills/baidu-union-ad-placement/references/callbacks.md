# 对外回调接口

对外接口与广告投放是**平行逻辑**。**不可以**在广告投放的 push 对象里新增 `closeAd`、`noAd` 等属性来监听事件，例如下面这种写法**无法**正常触发回调：

```javascript
// 错误示例：回调塞进投放对象，不会触发
(window.slotbydup = window.slotbydup || []).push({
  id: "u6341556",
  container: "_gpunkxjudct",
  closeAd: function () {} // ❌ 无效
});
```

正确做法是**独立 push** 回调对象，且每种回调在一个页面内**只定义一次**。

## 4.1 广告关闭接口 closeAd

用户点击"广告关闭"后触发。一个页面只需定义一次。

```javascript
(window.slotbydup = window.slotbydup || []).push({
  // 广告关闭回调方法，一个页面只需定义一个
  closeAd: function (tu_index) {
    // tu_index：同页面内相同代码位 id 的自增索引
    console.log(tu_index);
  }
});
```

| 参数 | 说明 |
|------|------|
| `tu_index` | 同页面内相同代码位 id 的自增索引，用于区分同一代码位的多个实例 |

## 4.2 无广告返回接口 noAd

无广告返回时触发。一个页面只需定义一次。

```javascript
(window.slotbydup = window.slotbydup || []).push({
  // 无广告返回回调方法，一个页面只需定义一个
  noAd: function (tu_index, noadInfo) {
    // tu_index：同页面内相同代码位 id 的自增索引
    console.log(tu_index);
    // noadInfo：无广告返回原因
    // { noadx: '联盟内部无广告返回状态码', queryid: '精确到本次检索的唯一 id' }
    console.log(noadInfo);
  }
});
```

| 参数 | 说明 |
|------|------|
| `tu_index` | 同页面内相同代码位 id 的自增索引 |
| `noadInfo.noadx` | 联盟内部无广告返回状态码 |
| `noadInfo.queryid` | 精确到本次检索的唯一 id |

**兜底方案**：除 `noAd` 回调外，平台打底设置中的"自定义链接"和"自动收起"也能满足大部分需求：
- **自定义链接**：无广告返回时，用合适的图片或页面作为填充内容。
- **自动收起**：无广告返回时销毁广告容器，避免页面出现空白窗口。

## 4.3 有广告返回接口 haveAd

有广告返回时触发。**该接口仅针对屏保代码位开放**，普通代码位不要使用。一个页面只需定义一次。

```javascript
(window.slotbydup = window.slotbydup || []).push({
  // 有广告返回的回调
  haveAd: function (tu_index) {
    // tu_index：同页面内相同代码位 id 的自增索引
    console.log(tu_index);
  }
});
```

| 参数 | 说明 |
|------|------|
| `tu_index` | 同页面内相同代码位 id 的自增索引 |

## 4.4 使用注意

- 三类回调均需**独立 push**，不能与广告投放 push 合并。
- 每种回调在一个页面内**只定义一次**，重复定义可能导致行为异常。
- `haveAd` 仅屏保代码位可用；普通 PC/WAP 代码位使用 `closeAd`、`noAd` 即可。
- 回调可结合前端 UI 逻辑（如关闭后调整布局、无广告时隐藏占位）使用。
