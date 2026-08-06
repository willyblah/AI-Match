<THREE_D_R3F>
# 3D 类：必须用 three.js（经 R3F）生成，禁止 2D Canvas + rAF。

Use for: 3D FPS / racing / third-person / endless runner / space sim.
**World rendering must use `three` via `@react-three/fiber` + `@react-three/drei`.**
React DOM only for HUD, menu, and result overlays.

**Forbidden for this genre:**
* HTML5 2D `canvas.getContext("2d")` + hand-rolled `requestAnimationFrame` as the
  3D world renderer
* Phaser / Pixi / raw WebGL without three.js
* Treating this genre like `platformer.md` / `brick_breaker.md` Canvas games

<PACKAGE_SELECTION>
* No synchronized 3D-specific `miaoda-game-*` packages in this trim.
* Gameplay authority stays in R3F `useFrame` + app state. Do not force-fit
  2D `grid-*` / `ballistics-*` unless the mechanic is truly planar math reused
  inside the 3D view — then open that genre doc and justify the reuse.
</PACKAGE_SELECTION>

<DEPENDENCIES>
Must be installed (not in the template):
```bash
pnpm add three @react-three/fiber @react-three/drei
# physics: pnpm add @react-three/rapier
# postprocessing: pnpm add @react-three/postprocessing
```
* **Required stack**: `three` is the scene/mesh/camera/light authority;
  `@react-three/fiber` mounts it; `@react-three/drei` for helpers.
* Do NOT pull in `pixi.js` or `framer-motion`. Drive the frame with R3F
  `useFrame`, not a page-level 2D canvas rAF loop.
* Three r150+ uses WebGL2; for WebGPU, explicitly upgrade to `three@0.16x+`.

<R3F_CANVAS_SETUP>
R3F's `<Canvas>` creates the WebGL surface for three.js — this is allowed.
It is **not** a substitute for writing 2D Canvas games.
```tsx
<Canvas
  shadows
  dpr={[1, 2]}                      // cap at 1 on mobile, max 2 on desktop to avoid frying 4K GPUs
  camera={{ position: [0, 4, 8], fov: 60 }}
  gl={{ antialias: true, powerPreference: "high-performance" }}
  onCreated={({ gl }) => gl.setClearColor("#101018")}
>
  <Scene />
</Canvas>
```
* Layer HUD as React DOM outside the Canvas. Use `<div className="absolute inset-0 pointer-events-none">` for the HUD layer; interactive UI gets its own block that re-enables pointer-events.
* **Do NOT** call `useThree` outside the Canvas; only inside Canvas children.

<SCENE_STRUCTURE>
```
<Scene>
  <ambientLight intensity={0.4} />
  <directionalLight castShadow position={[10,10,5]} intensity={1.2} />
  <Suspense fallback={null}>
    <Player />
    <Enemies />
    <Terrain />
    <Environment preset="sunset" />
  </Suspense>
  <PostProcessing />
</Scene>
```
* Wrap anything loading textures/GLTF in `<Suspense>`; show `<Html center>Loading…</Html>` or a plain placeholder while loading.
* At most 2–3 dynamic lights; the rest via baked lightmaps or environment maps.
</SCENE_STRUCTURE>

<GAME_LOOP>
```tsx
useFrame((state, dt) => {
  // dt is in seconds; frame-rate-independent movement: v * dt
  updatePlayer(dt);
  updateEnemies(dt);
});
```
* R3F already runs rAF internally; do NOT start your own `requestAnimationFrame`.
* `state.clock.getElapsedTime()` gives total elapsed time; `state.camera` gives the main camera.
* Pause: early-return inside `useFrame`, or use `<Canvas frameloop="demand">` and call `invalidate()` manually.
</GAME_LOOP>

<STATE_MODEL>
* **Realtime values** use `useRef` (position, velocity, hp); mutate `ref.current.x` each frame.
* **UI-facing values** use `useState` or Zustand (after installing zustand, write a `create` store).
* Share realtime data between components via zustand's `getState()` directly — don't pass it through props every frame.
</STATE_MODEL>

<CONTROLS>
* **PointerLock (FPS)**: `import { PointerLockControls } from "@react-three/drei"`; click the canvas to lock the mouse, ESC to unlock.
* **Orbit (free look)**: `OrbitControls` for showcase/editor cameras, not for combat games.
* **Third-person**: write your own `useFrame` that computes a camera offset from player.position: `cam.position.lerp(target, 5*dt)`.
* **Vehicle**: `@react-three/rapier`'s `useRapier` + `RigidBody` + vehicle control (accel + steering); avoid hand-rolling vehicle physics.
* **Mobile**: nipplejs or a custom DOM joystick; write joystick input to a useRef and read it in `useFrame`.
</CONTROLS>

<PHYSICS>
* Simple collision (walls, pickups): AABB or sphere-distance checks inside `useFrame` are enough.
* Complex physics (vehicles, stacking, destruction): install `@react-three/rapier`:
  ```tsx
  <Physics>
    <RigidBody colliders="cuboid"><mesh>...</mesh></RigidBody>
  </Physics>
  ```
* **Don't** run cannon-es and rapier together; pick one. Default to rapier (faster, more active).
</PHYSICS>

<ASSETS>
* GLTF loading: `useGLTF("/models/player.glb")` (drei); put models in `public/models/`; Vite serves them in dev.
* Textures: `useTexture("/textures/grass.jpg")`; enable `wrapS/T = RepeatWrapping` and set `repeat`.
* **Preload**: at the entry, `useGLTF.preload("/models/player.glb")` to avoid a hitch on first spawn.
* Prefer Draco/Meshopt compression: process with `gltf-transform`; aim for total models < 10MB.
* Audio: `PositionalAudio` (drei) for 3D sound; resume `AudioContext` after the first gesture.
</ASSETS>

<PERFORMANCE>
* **Instancing**: use `<Instances>` / `<InstancedMesh>` for repeated objects (trees, grass, bullets). Thousands in one draw call.
* **LOD**: drei `Detailed`, or swap models by distance yourself.
* **Frustum culling**: on by default; set entity bounds correctly so they aren't wrongly culled.
* **Shadow map**: 1024/2048 is plenty; keep `shadow.camera.far` within the scene diameter.
* **DPR**: `<Canvas dpr={[1,2]}>` prevents frying 4K GPUs; drop to `gl.setPixelRatio(1)` under load.
* **Postprocessing** is expensive: Bloom with a dedicated mip pass saves VRAM; disable SSAO on mobile.
* **In useFrame**, avoid allocating new objects: use `.position.set(x,y,z)` or `vec3.copy()`, not `new THREE.Vector3()`.
* Target: 60fps desktop, 30fps mobile; monitor with `<Stats />` (drei).
</PERFORMANCE>

<CAMERA>
* FPS: camera follows player.position + eye offset (0, 1.6, 0). Rotation from PointerLock; rotating the player rotates the camera.
* Third-person: camera behind and above the player; `useFrame`: `cam.position.lerp(player.position.clone().add(offset), 5*dt); cam.lookAt(player.position)`.
* Racing: follow the car, lookAt an offset ahead; drift lag comes from the lerp coefficient.
* Cutscene: drei `useSpring` (react-spring/three) for camera transitions; avoid framer-motion.
</CAMERA>

<UI_INTEGRATION>
* HUD / health bars / ammo: React DOM absolutely positioned over the Canvas.
* World-space UI (health bar over an enemy's head): drei `<Html>` or a `sprite` texture. `<Html>` is convenient but costly — fine for dozens, switch to sprites for hundreds.
* Result / pause: shadcn `Dialog` over the whole screen; flip the game phase in `onOpenChange`.
* Tutorial hints: drei `<Html distanceFactor={10}>` speech bubbles anchored to world coordinates.
</UI_INTEGRATION>

<AUDIO_3D>
* BGM uses a plain `<audio>`; scene SFX use `PositionalAudio` (drei) attached to a mesh, attenuating with distance.
* Unlock audio on first click; `state.camera.add(listener)`.
</AUDIO_3D>

<SERIALIZATION>
* Save: position, rotation, quest state, gold, etc. Convert `three` Vector3/Quaternion to `[x,y,z]` before serializing.
* Level data JSON: `{ obstacles: [{pos, rot, scale, kind}], ... }`; instantiate `<Obstacle>` by kind at runtime.
</SERIALIZATION>

<PITFALLS>
* **setState inside useFrame — CRITICAL**: a React update every frame tanks performance. Mutate position via ref; only setState for UI-visible values (score, hp) and throttle it (e.g. 5 Hz).
* **`new THREE.Vector3()` in JSX**: rebuilds objects every frame, GC thrash. Use `useMemo` or declare as a const.
* **Suspense without a fallback**: loading shows a black screen or throws. Wrap every GLTF/texture in Suspense + fallback.
* **Shadow map too large**: shadows get MORE jagged. Start at 1024/2048 and test.
* **Multiple `Canvas` elements**: a common beginner mistake — multiple Canvases on one page blow up VRAM. A whole game needs only one.
* **Forgetting to dispose**: navigating away auto-unloads the Canvas and frees the GPU; but if you `new`'d a Renderer manually, call `renderer.dispose()`.
* **Mobile pinch-zoom interference**: add `touch-action: none` on the Canvas parent container.
* **Camera near/far spread too large**: causes z-fighting; keep near=0.1, far within 1000.
</PITFALLS>

<COMPLETENESS>
* Full five-step flow: main menu → play → pause → result.
* At least 1 scene + 3 entity types (character, enemy, pickup).
* Stable 60fps desktop; degrading to 30fps mobile is acceptable.
* Graphics options: low / medium / high (shadows, postprocessing, DPR).
* localStorage stores best score and completion flag.
* `pnpm lint` passes; no console warnings (fix `three` version mismatch, `shaderMaterial uniform undefined`, etc.).
</COMPLETENESS>
</THREE_D_R3F>
