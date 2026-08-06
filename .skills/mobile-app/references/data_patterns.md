# Data Patterns Reference

## HTTP Requests with expo/fetch

```tsx
import { fetch } from "expo/fetch";

const fetchData = async (url: string) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
  return response.json();
};
```

## Authentication Token Storage

```tsx
import * as SecureStore from "expo-secure-store";

await SecureStore.setItemAsync("auth_token", token);
const token = await SecureStore.getItemAsync("auth_token");
```

`expo-secure-store` is iOS/Android only — it is NOT stubbed on Web and **throws on call**. Wrap it with a `process.env.EXPO_OS === "web"` branch that falls back to `localStorage`:

```tsx
const setItem = (k: string, v: string) =>
  process.env.EXPO_OS === "web"
    ? Promise.resolve(localStorage.setItem(k, v))
    : SecureStore.setItemAsync(k, v);

const getItem = (k: string) =>
  process.env.EXPO_OS === "web"
    ? Promise.resolve(localStorage.getItem(k))
    : SecureStore.getItemAsync(k);
```

## React Query Pattern

For complex data fetching with caching:

```tsx
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 1000 * 60 * 5 } } });

export default function RootLayout() {
  return <QueryClientProvider client={queryClient}>{/* ... */}</QueryClientProvider>;
}

function ProductList() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["products"],
    queryFn: () => supabase.from("products").select("*"),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) return <ActivityIndicator />;
  if (error) return <Text className="text-destructive">Failed to load</Text>;
}

const mutation = useMutation({
  // newTask must NOT contain the owner column (the one declared NOT NULL DEFAULT auth.uid()) — the DB auto-fills it
  mutationFn: (newTask) => supabase.from("tasks").insert(newTask),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
});
```

## Offline Handling

```tsx
import * as Network from "expo-network";

const networkState = await Network.getNetworkStateAsync();
if (!networkState.isConnected) {
  setOffline(true);
  return;
}

{isOffline && <Text className="text-muted-foreground">No internet connection. Pull to retry.</Text>}
```

## expo-sqlite (Async APIs Only)

ONLY use async APIs — sync APIs crash on Web. Use a `dbReady` Promise pattern:

```typescript
// src/lib/database.ts
import * as SQLite from "expo-sqlite";

const dbReady = SQLite.openDatabaseAsync("app.db").then(async (db) => {
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      done INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now'))
    );
  `);
  return db;
});

export async function getAllTasks() {
  const db = await dbReady;
  return db.getAllAsync<{ id: number; title: string; done: number }>("SELECT * FROM tasks ORDER BY created_at DESC");
}

export async function insertTask(title: string) {
  const db = await dbReady;
  return db.runAsync("INSERT INTO tasks (title) VALUES (?)", [title]);
}

export async function updateTask(id: number, done: boolean) {
  const db = await dbReady;
  return db.runAsync("UPDATE tasks SET done = ? WHERE id = ?", [done ? 1 : 0, id]);
}
```

Call exported async functions in `useFocusEffect` or event handlers:

```tsx
import { useFocusEffect } from "expo-router";
import { getAllTasks } from "@/lib/database";

export default function TasksScreen() {
  const [tasks, setTasks] = useState([]);
  useFocusEffect(useCallback(() => { getAllTasks().then(setTasks); }, []));
}
```