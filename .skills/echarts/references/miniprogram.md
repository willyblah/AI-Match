# Taro + React 微信小程序 ECharts 集成

基于 Taro 4 + React 实现，支持微信小程序与 H5 双端。直接将以下文件复制到项目中即可使用，无需 `echarts-for-weixin`。

---

## 一、依赖安装

```bash
pnpm add echarts
```

---

## 二、目录结构

将以下文件整体复制到 `src/components/echarts/`：

```
src/components/echarts/
├── index.ts               # 导出入口
├── echart/
│   └── index.tsx          # EChart 封装组件（按需注册图表模块）
└── ec-canvas/
    ├── index.tsx          # 小程序 Canvas 桥接层
    ├── wx-canvas.js       # WxCanvas 适配器（适配微信小程序 Canvas 2D API）
    └── index.scss
```

---

## 三、文件源码

### `index.ts`

```ts
export { default as EChart } from "./echart";
export { default as EcCanvas } from "./ec-canvas";
```

---

### `echart/index.tsx`

按需引入 ECharts 模块，控制包体积。**新增图表类型时，在此文件的 import 和 `echarts.use([...])` 中同步追加对应模块。**

```tsx
import React, { Component, createRef } from "react";
import * as echarts from "echarts/core";
import {
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  FunnelChart,
  GaugeChart,
  RadarChart,
  HeatmapChart,
} from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { View } from "@tarojs/components";
import EcCanvasTaro, { ECObj } from "../ec-canvas";

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  FunnelChart,
  GaugeChart,
  RadarChart,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

const isH5 = process.env.TARO_ENV === "h5";

interface BaseChartState {
  ec: ECObj;
}

interface BaseChartProps {
  canvasId: string;
  onClick?: (params: unknown) => void;
  onDblclick?: (params: unknown) => void;
  onMousewheel?: (params: unknown) => void;
  onMouseout?: (params: unknown) => void;
  onMouseup?: (params: unknown) => void;
  onMousemove?: (params: unknown) => void;
  onMousedown?: (params: unknown) => void;
}

class BaseChart extends Component<BaseChartProps, BaseChartState> {
  state = {
    ec: {
      lazyLoad: true,
    },
  };

  Chart: any;
  h5DomRef = createRef<HTMLDivElement>();
  h5Chart: any = null;

  // 外部通过 ref 调用此方法渲染图表，传入标准 ECharts option
  refresh = (data: any) => {
    if (isH5) {
      this.refreshH5(data);
    } else {
      this.refreshWeapp(data);
    }
  };

  refreshH5 = (data: any) => {
    const dom = this.h5DomRef.current;
    if (!dom) return;
    if (!this.h5Chart) {
      this.h5Chart = echarts.init(dom);
      this.bindEvents(this.h5Chart);
    }
    this.h5Chart.setOption(data);
  };

  refreshWeapp = (data: any) => {
    this.Chart.init((canvas, width, height, canvasDpr) => {
      const chart = echarts.init(canvas, null, {
        width: width,
        height: height,
        devicePixelRatio: canvasDpr,
      });
      canvas.setChart(chart);
      chart.setOption(data);
      this.bindEvents(chart);
      return chart;
    });
  };

  bindEvents = (chart: any) => {
    const { onClick, onDblclick, onMousewheel, onMouseout, onMouseup, onMousemove, onMousedown } = this.props;
    if (onClick) chart.on("click", onClick);
    if (onDblclick) chart.on("dblclick", onDblclick);
    if (onMousewheel) chart.on("mousewheel", onMousewheel);
    if (onMouseout) chart.on("mouseout", onMouseout);
    if (onMouseup) chart.on("mouseup", onMouseup);
    if (onMousedown) chart.on("mousedown", onMousedown);
    if (onMousemove) chart.on("mousemove", onMousemove);
  };

  componentWillUnmount() {
    if (this.h5Chart) {
      this.h5Chart.dispose();
      this.h5Chart = null;
    }
  }

  refChart = (node) => (this.Chart = node);

  render() {
    const { canvasId } = this.props;
    if (isH5) {
      return (
        <View style={{ width: "100%", height: "100%" }}>
          <div ref={this.h5DomRef} style={{ width: "100%", height: "100%" }} />
        </View>
      );
    }
    return (
      <EcCanvasTaro
        ref={this.refChart}
        canvasId={canvasId}
        ec={this.state.ec}
      />
    );
  }
}

export default BaseChart;
```

---

### `ec-canvas/index.tsx`

> **重要**：此文件必须用 `echarts/core`，不能用全量 `import * as echarts from "echarts"`，否则按需引入失效，vendors.js 将超过 1MB。

```tsx
import Taro from "@tarojs/taro";
import React, { Component } from "react";
import { Canvas } from "@tarojs/components";
import * as echarts from "echarts/core";
import WxCanvas from "./wx-canvas";
import "./index.scss";

function wrapTouch(event) {
  for (let i = 0; i < event.touches.length; ++i) {
    const touch = event.touches[i];
    touch.offsetX = touch.x;
    touch.offsetY = touch.y;
  }
  return event;
}

export interface EcCanvasState {}

export interface ECObj {
  onInit?(canvas, width, height, dpr): void;
  lazyLoad?: boolean;
}

export interface EcCanvasProps {
  canvasId: string;
  ec: ECObj;
}

interface EcCanvasTaro {
  canvasNode: any;
  chart: any;
}

class EcCanvasTaro extends Component<EcCanvasProps, EcCanvasState> {
  componentDidMount() {
    echarts.registerPreprocessor((option) => {
      if (option && option.series) {
        if (option.series.length > 0) {
          option.series.forEach((series) => {
            series.progressive = 0;
          });
        } else if (typeof option.series === "object") {
          option.series.progressive = 0;
        }
      }
    });

    if (!this.props.ec) {
      console.warn(
        '组件需绑定 ec 变量，例：<ec-canvas id="mychart-dom-bar" ' +
          'canvas-id="mychart-bar" ec="{{ ec }}"></ec-canvas>'
      );
      return;
    }
    if (!this.props.ec.lazyLoad) {
      this.init();
    }
  }

  init(callback?) {
    setTimeout(() => {
      this.initByNewWay(callback);
    }, 30);
  }

  initByNewWay(callback?) {
    const query = Taro.createSelectorQuery();
    const { ec, canvasId } = this.props;
    query
      .select(`.ec-canvas.${canvasId}`)
      .fields({
        node: true,
        size: true,
      })
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) return;
        const canvasNode = res[0].node;
        this.canvasNode = canvasNode;
        const canvasDpr = Taro.getWindowInfo?.()?.pixelRatio ?? Taro.getSystemInfoSync().pixelRatio;
        const canvasWidth = res[0].width;
        const canvasHeight = res[0].height;
        const ctx = canvasNode.getContext("2d");
        const canvas = new WxCanvas(ctx, canvasId, true, canvasNode);
        echarts.setCanvasCreator(() => {
          return canvas;
        });
        if (typeof callback === "function") {
          this.chart = callback(canvas, canvasWidth, canvasHeight, canvasDpr);
        } else if (typeof ec.onInit === "function") {
          this.chart = ec.onInit(canvas, canvasWidth, canvasHeight, canvasDpr);
        }
      });
  }

  touchStart = (e) => {
    if (this.chart && e.touches.length > 0) {
      var touch = e.touches[0];
      var handler = this.chart.getZr().handler;
      handler.dispatch("mousedown", {
        zrX: touch.x,
        zrY: touch.y,
      });
      handler.dispatch("mousemove", {
        zrX: touch.x,
        zrY: touch.y,
      });
      handler.processGesture(wrapTouch(e), "start");
    }
  };

  touchMove = (e) => {
    if (this.chart && e.touches.length > 0) {
      var touch = e.touches[0];
      var handler = this.chart.getZr().handler;
      handler.dispatch("mousemove", {
        zrX: touch.x,
        zrY: touch.y,
      });
      handler.processGesture(wrapTouch(e), "change");
    }
  };

  touchEnd = (e) => {
    if (this.chart) {
      const touch = e.changedTouches ? e.changedTouches[0] : {};
      var handler = this.chart.getZr().handler;
      handler.dispatch("mouseup", {
        zrX: touch.x,
        zrY: touch.y,
      });
      handler.dispatch("click", {
        zrX: touch.x,
        zrY: touch.y,
      });
      handler.processGesture(wrapTouch(e), "end");
    }
  };

  render() {
    const { canvasId } = this.props;
    return (
      <Canvas
        type="2d"
        className={`ec-canvas ${canvasId}`}
        canvasId={canvasId}
        onTouchStart={this.touchStart}
        onTouchMove={this.touchMove}
        onTouchEnd={this.touchEnd}
      />
    );
  }
}

export default EcCanvasTaro;
```

---

### `ec-canvas/wx-canvas.js`

```js
export default class WxCanvas {
  constructor(ctx, canvasId, isNew, canvasNode) {
    this.ctx = ctx;
    this.canvasId = canvasId;
    this.chart = null;
    this.isNew = isNew;
    if (isNew) {
      this.canvasNode = canvasNode;
    } else {
      this._initStyle(ctx);
    }
    this._initEvent();
  }

  getContext(contextType) {
    if (contextType === "2d") {
      return this.ctx;
    }
  }

  setChart(chart) {
    this.chart = chart;
  }

  addEventListener() {
    // noop
  }

  attachEvent() {
    // noop
  }

  detachEvent() {
    // noop
  }

  _initCanvas(zrender, ctx) {
    zrender.util.getContext = function () {
      return ctx;
    };
    zrender.util.$override("measureText", function (text, font) {
      ctx.font = font || "12px sans-serif";
      return ctx.measureText(text);
    });
  }

  _initStyle(ctx) {
    ctx.createRadialGradient = () => {
      return ctx.createCircularGradient(arguments);
    };
  }

  _initEvent() {
    this.event = {};
    const touchEndEvents = ["touchEnd"];
    const eventNames = [
      { wxName: "touchStart", ecName: "mousedown" },
      { wxName: "touchMove",  ecName: "mousemove" },
      { wxName: "touchEnd",   ecName: "mouseup" },
      { wxName: "touchEnd",   ecName: "click" },
    ];
    eventNames.forEach((name) => {
      this.event[name.wxName] = (e) => {
        const touch = touchEndEvents.includes(name.wxName)
          ? e.changedTouches && e.changedTouches[0]
          : e.touches[0];
        if (!touch) return;
        this.chart.getZr().handler.dispatch(name.ecName, {
          zrX: touch.x,
          zrY: touch.y,
          preventDefault: () => {},
          stopImmediatePropagation: () => {},
          stopPropagation: () => {},
        });
      };
    });
  }

  set width(w) {
    if (this.canvasNode) this.canvasNode.width = w;
  }
  set height(h) {
    if (this.canvasNode) this.canvasNode.height = h;
  }
  get width() {
    if (this.canvasNode) return this.canvasNode.width;
    return 0;
  }
  get height() {
    if (this.canvasNode) return this.canvasNode.height;
    return 0;
  }
}
```

---

### `ec-canvas/index.scss`

```scss
.ec-canvas {
  width: 100%;
  height: 100%;
  display: block;
}
```

---

## 四、页面中使用

**通用模式**：通过 `ref` 获取组件实例，调用 `ref.refresh(option)` 传入标准 ECharts option。

- `canvasId` 在整个小程序中必须唯一
- `setTimeout` 延迟 300ms 是为了等待 Canvas 节点渲染完毕后再初始化

```tsx
import React, { Component } from "react";
import { View } from "@tarojs/components";
import { EChart } from "../../components/echarts";

export default class MyChartPage extends Component {
  chart: any;

  componentDidMount() {
    const option = {
      // 标准 ECharts option
    };
    setTimeout(() => {
      this.chart.refresh(option);
    }, 300);
  }

  render() {
    return (
      <View style={{ width: "100%", height: "100vh" }}>
        <EChart ref={(node) => (this.chart = node)} canvasId="my-chart" />
      </View>
    );
  }
}
```

**事件绑定**：

```tsx
<EChart
  ref={(node) => (this.chart = node)}
  canvasId="bar-canvas"
  onClick={(params) => console.log("点击", params)}
  onDblclick={(params) => console.log("双击", params)}
/>
```

---

## 五、各图表类型 option 示例

**折线图**
```ts
const option = {
  xAxis: {},
  yAxis: {},
  series: [{ type: "line", data: [[20, 120], [50, 200], [40, 50]] }],
};
```

**柱状图**
```ts
const option = {
  xAxis: { type: "category", data: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] },
  yAxis: { type: "value" },
  series: [{
    type: "bar",
    data: [120, 200, 150, 80, 70, 110, 130],
    showBackground: true,
    backgroundStyle: { color: "rgba(220,220,220,0.8)" },
  }],
};
```

**饼图**
```ts
const option = {
  title: { text: "用户访问来源", left: "center" },
  tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c} ({d}%)" },
  legend: { orient: "vertical", left: "left" },
  series: [{
    name: "访问来源",
    type: "pie",
    radius: "55%",
    center: ["50%", "60%"],
    data: [
      { value: 335, name: "直接访问" },
      { value: 310, name: "邮件营销" },
      { value: 234, name: "联盟广告" },
    ],
  }],
};
```

**散点图**
```ts
const option = {
  xAxis: {},
  yAxis: {},
  series: [{
    type: "scatter",
    symbolSize: 20,
    data: [[10.0, 8.04], [8.0, 6.95], [13.0, 7.58], [9.0, 8.81]],
  }],
};
```

**漏斗图**
```ts
const option = {
  title: { text: "漏斗图" },
  tooltip: { trigger: "item", formatter: "{a} <br/>{b} : {c}%" },
  legend: { data: ["展现", "点击", "访问", "咨询", "订单"] },
  series: [{
    name: "漏斗图",
    type: "funnel",
    left: "10%", width: "80%", top: 60, bottom: 60,
    sort: "descending", gap: 2,
    data: [
      { value: 100, name: "展现" }, { value: 80, name: "点击" },
      { value: 60, name: "访问" }, { value: 40, name: "咨询" },
      { value: 20, name: "订单" },
    ],
  }],
};
```

**仪表盘**
```ts
const option = {
  tooltip: { formatter: "{a} <br/>{b} : {c}%" },
  series: [{
    name: "业务指标",
    type: "gauge",
    detail: { formatter: "{value}%" },
    data: [{ value: 50, name: "完成率" }],
  }],
};
```

**雷达图**
```ts
const option = {
  title: { text: "基础雷达图" },
  radar: {
    indicator: [
      { name: "销售", max: 6500 },
      { name: "管理", max: 16000 },
      { name: "研发", max: 30000 },
    ],
  },
  series: [{
    name: "预算 vs 开销",
    type: "radar",
    data: [
      { value: [4300, 10000, 28000], name: "预算" },
      { value: [5000, 14000, 20000], name: "实际" },
    ],
  }],
};
```

**热力图**（需已注册 `VisualMapComponent`，默认已包含）
```ts
const option = {
  tooltip: { position: "top" },
  animation: false,
  grid: { height: "50%", top: "10%" },
  xAxis: { type: "category", data: hours, splitArea: { show: true } },
  yAxis: { type: "category", data: days, splitArea: { show: true } },
  visualMap: { min: 0, max: 10, calculable: true, orient: "horizontal", left: "center", bottom: "15%" },
  series: [{
    name: "Punch Card",
    type: "heatmap",
    data: data,  // [[x_index, y_index, value], ...]
    label: { show: true },
    emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
  }],
};
```

---

## 六、新增图表类型

在 `echart/index.tsx` 的 import 和 `echarts.use([...])` 中同步追加，例如新增 K 线图：

```ts
import { CandlestickChart } from "echarts/charts";
import { DataZoomComponent } from "echarts/components";

echarts.use([
  // ...原有模块
  CandlestickChart,
  DataZoomComponent,
]);
```

常用模块速查：

| 图表类型 | 导入名（来自 echarts/charts） |
|---------|------------------------------|
| 折线图 | `LineChart` |
| 柱状图 | `BarChart` |
| 饼图 | `PieChart` |
| 散点图 | `ScatterChart` |
| 漏斗图 | `FunnelChart` |
| 仪表盘 | `GaugeChart` |
| 雷达图 | `RadarChart` |
| 热力图 | `HeatmapChart` |
| K 线图 | `CandlestickChart` |
| 地图 | `MapChart` |
| 树图 | `TreeChart` |
| 矩形树图 | `TreemapChart` |
| 桑基图 | `SankeyChart` |

| 组件 | 导入名（来自 echarts/components） |
|-----|----------------------------------|
| 标题 | `TitleComponent` |
| 提示框 | `TooltipComponent` |
| 图例 | `LegendComponent` |
| 直角坐标系 | `GridComponent` |
| 视觉映射 | `VisualMapComponent` |
| 数据缩放 | `DataZoomComponent` |
| 工具栏 | `ToolboxComponent` |
| 极坐标系 | `PolarComponent` |
| 时间轴 | `TimelineComponent` |

---

## 七、注意事项

- **颜色格式**：不使用 `hsla` 作为透明颜色写法；需要透明色时使用 `rgba`，不透明色使用 `rgb`。
- **避免数据点不显示**：`itemStyle.color` 若设为 `'#fff'`，在浅色背景卡片上会与背景融为一体，看起来像数据点消失、断点一样，应设为线条颜色：

  ```ts
  series: [{
    type: "line",
    itemStyle: { color: color }, // color 不要用 '#fff'
    data: [{ value: 100, itemStyle: { color: color } }],
  }],
  ```
