# miaoda-game-grid-react

React bindings for observable rectangular grid cells, selection, path previews, and movement areas. It complements `grid-piece-react` and `grid-vision-react`; rendering and input remain application concerns.

```sh
pnpm add miaoda-game-grid-react miaoda-game-grid-core
```

Use `GridController`, `useGridController`, and `useGridView`. Mutations publish row-major cells; path and area queries publish detached results suitable for DOM/CSS, SVG, canvas overlays, or editor tools.
