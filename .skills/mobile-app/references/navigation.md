# Navigation Reference

## Stack-wrapping-Tabs Architecture

Directory structure:
```
src/app/(app)/
  _layout.tsx        ← Stack (keep as Stack, from boilerplate)
  (tabs)/
    _layout.tsx      ← Tabs (ONLY visible tab screens here)
    home.tsx         ← Home tab (NOT index.tsx — avoids URL collision with root index.tsx)
    tasks.tsx        ← Tasks tab
  tasks/
    _layout.tsx      ← Stack (REQUIRED for subdirectories with dynamic routes)
    [id].tsx         ← Detail page (pushed onto Stack above Tabs)
    create.tsx
  settings.tsx       ← Non-tab page (pushed onto Stack)
```

`(app)/_layout.tsx`:
```tsx
import { Stack } from "expo-router";

export default function AppLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
    </Stack>
  );
}
```

`(app)/(tabs)/_layout.tsx`:
```tsx
import { Tabs } from "expo-router";
import { Home, List } from "lucide-react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#007AFF",
        tabBarStyle: {
          height: 68 + insets.bottom,
          paddingBottom: insets.bottom,
        },
      }}
      initialRouteName="home"
    >
      <Tabs.Screen name="home" options={{ title: "Home", tabBarIcon: ({ color, size }) => <Home size={size} color={color} /> }} />
      <Tabs.Screen name="tasks" options={{ title: "Tasks", tabBarIcon: ({ color, size }) => <List size={size} color={color} /> }} />
    </Tabs>
  );
}
```

Navigating from tab to detail page:
```tsx
router.push(`/(app)/tasks/${id}`);
```

## Entry Point

`src/app/index.tsx` is the landing page component in the boilerplate. When the app uses auth routing (Stack.Protected), do NOT replace it with a Redirect — it serves as the unauthenticated screen.

## No-Auth Setup

When the app does NOT require login, simplify the boilerplate:

1. Simplify root `_layout.tsx` (remove SessionProvider + Stack.Protected, keep Sentry.init if present):
```tsx
import { Stack } from "expo-router";
import { PortalHost } from "@rn-primitives/portal";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import "../global.css";

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
      </Stack>
      <PortalHost />
    </GestureHandlerRootView>
  );
}
```

2. Delete `(auth)/` directory and `src/ctx.tsx`

3. Use `index.tsx` as home page directly (no tabs) or redirect to `/home` (with tabs):
```tsx
import { Redirect } from "expo-router";

export default function Index() {
  return <Redirect href="/home" />;
}
```

4. No-auth directory structure with tabs:
```
src/app/
  _layout.tsx        ← Stack (simplified, no auth)
  index.tsx          ← <Redirect href="/home" /> or home content directly
  (tabs)/
    _layout.tsx      ← Tabs (initialRouteName="home")
    home.tsx         ← Home tab
    explore.tsx
  details/
    _layout.tsx      ← Stack
    [id].tsx         ← Detail page
```

## Dynamic Routes

```
src/app/(app)/tasks/
  [id]/
    _layout.tsx  ← Stack
    index.tsx    ← Single item detail (NOT [id].tsx at parent level)
    edit.tsx     ← sibling sub-page
```
NEVER place `[id].tsx` and a `[id]/` directory at the same level — duplicate Screen, runtime crash. Use `[id]/index.tsx` for the detail page.

Access params:
```tsx
const { id } = useLocalSearchParams<{ id: string }>();
```

## useFocusEffect — Data Refresh on Navigation Return

```tsx
useFocusEffect(useCallback(() => { loadData(); }, [loadData]));
```

Full example with Supabase:
```tsx
export default function TasksScreen() {
  const [tasks, setTasks] = useState([]);
  const loadTasks = async () => { const { data } = await supabase.from("tasks").select("*"); setTasks(data ?? []); };
  useFocusEffect(useCallback(() => { loadTasks(); }, [loadTasks]));
}
```

## Page Navigation

```tsx
<Link href="/profile/settings"><Text>Go to Settings</Text></Link>

const router = useRouter();
router.push("/profile/settings");
router.replace("/");   // removes current screen from back-stack
router.back();
```

NEVER call `router.push` / `router.back` / `router.replace` imperatively during first render or in a mount `useEffect` — the Root Layout isn't mounted yet, so on a Web refresh of a sub-route this leaves a blank/white screen. For "no data → leave this screen", render a declarative `<Redirect href=... />` instead:

```tsx
if (!item) return <Redirect href={"/(app)/tasks" as RelativePathString} />;
```

## Modal & Form Sheet

```tsx
<Stack.Screen name="modal" options={{ presentation: "modal" }} />
<Stack.Screen name="sheet" options={{ presentation: "formSheet", sheetGrabberVisible: true, sheetAllowedDetents: [0.5, 1.0] }} />
```