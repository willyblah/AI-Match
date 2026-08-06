# Components Reference

## Pull-to-Refresh

```tsx
const [refreshing, setRefreshing] = useState(false);

const onRefresh = useCallback(async () => {
  setRefreshing(true);
  try { await loadData(); } finally { setRefreshing(false); }
}, []);

<FlatList
  data={data}
  refreshing={refreshing}
  onRefresh={onRefresh}
  contentInsetAdjustmentBehavior="automatic"
  renderItem={({ item }) => ...}
/>
```

## KeyboardAvoidingView

```tsx
<KeyboardAvoidingView behavior={process.env.EXPO_OS === "ios" ? "padding" : "height"} className="flex-1">
  <ScrollView contentContainerClassName="flex-grow justify-center px-6" keyboardShouldPersistTaps="handled">
    <TextInput returnKeyType="next" onSubmitEditing={() => nextRef.current?.focus()} />
    <TextInput ref={nextRef} returnKeyType="done" />
    <Pressable className="bg-primary rounded-xl p-4 items-center" onPress={handleSubmit}>
      <Text className="text-primary-foreground font-semibold">Submit</Text>
    </Pressable>
  </ScrollView>
</KeyboardAvoidingView>
```

## Status Bar

```tsx
import { StatusBar } from "expo-status-bar";

// Light header → style="dark"; dark header → style="light"
// Android MUST also set backgroundColor to match header
<StatusBar style="dark" backgroundColor="#ffffff" />
```

## Loading States

```tsx
if (isLoading) {
  return <View className="flex-1 items-center justify-center"><ActivityIndicator size="large" className="text-primary" /></View>;
}

// Inline (e.g., FlatList footer)
<ActivityIndicator size="small" className="text-muted-foreground my-4" />
```

## Empty States

```tsx
const EmptyState = () => (
  <View className="flex-1 items-center justify-center py-16 gap-3">
    <ClipboardList size={48} className="text-muted-foreground" />
    <Text className="text-lg font-semibold text-foreground">No items yet</Text>
  </View>
);

<FlatList data={items} ListEmptyComponent={<EmptyState />} ... />
```

## Error Handling UX

```tsx
{error && (
  <View className="items-center p-6 gap-3">
    <Text className="text-destructive text-center">{error}</Text>
    <Pressable className="bg-primary rounded-lg px-6 py-3" onPress={loadData}>
      <Text className="text-primary-foreground font-medium">Retry</Text>
    </Pressable>
  </View>
)}

{fieldError && <Text className="text-destructive text-sm mt-1">{fieldError}</Text>}

{permissionDenied && (
  <Text className="text-destructive text-sm mt-2">
    Camera access is required. Please enable it in Settings → App → Camera.
  </Text>
)}
```

## Instant Touch Feedback

```tsx
<Pressable
  className="active:opacity-70"
  android_ripple={{ color: "rgba(0,0,0,0.1)" }}
  onPress={handlePress}
>
  <Text className="text-base">Press me</Text>
</Pressable>
```

## ScrollView as Sidebar

Wrap ScrollView in a parent `View` with explicit `width` to constrain sidebar width:

```tsx
<View style={{ width: 80, flexShrink: 0 }}>
  <ScrollView style={{ flex: 1 }}>
    {/* sidebar content */}
  </ScrollView>
</View>
```

## Form Sheet

```tsx
<Stack.Screen name="sheet" options={{ presentation: "formSheet", sheetGrabberVisible: true, sheetAllowedDetents: [0.5, 1.0] }} />
```

## Infinite Scroll

```tsx
<FlatList
  data={items}
  onEndReached={loadMore}
  onEndReachedThreshold={0.5}
  ListFooterComponent={isFetchingMore ? <ActivityIndicator size="small" className="text-muted-foreground my-4" /> : null}
/>
```

## Carousel / Horizontal Paging

Carousels (image sliders, onboarding, step wizards) break on react-native-web in three specific ways — follow all three rules:

1. Give each horizontal `FlatList` / `ScrollView` item a **fixed width** (e.g. `SCREEN_WIDTH` from `useWindowDimensions`). NEVER add a main-axis `flex-1` to the item — on rn-web that divides one screen across all items so paging never advances.
2. Make `currentIndex` **state** the source of truth: a Next button calls `setCurrentIndex`, and `scrollToIndex` is only for visual sync. NEVER drive step state purely off scroll position.
3. In `onViewableItemsChanged`, only update the index when `viewableItems.length === 1` — rn-web reports ALL items visible at once, which otherwise pins `index` at `0`.

## Splash Screen

```bash
pnpm exec expo install expo-splash-screen
```

```tsx
SplashScreen.preventAutoHideAsync();
// after async init completes:
await SplashScreen.hideAsync();
```

## Date/Time Picker

Use `react-native-ui-datepicker` (pure JS, no native modules, works on Web):

```bash
pnpm exec expo install react-native-ui-datepicker
```

```tsx
import DateTimePicker from "react-native-ui-datepicker";

const [date, setDate] = useState(new Date());

<DateTimePicker
  mode="single"
  date={date}
  onChange={(params) => setDate(params.date)}
/>
```

## Icon Mapping Table

Use `lucide-react-native` (pre-installed) for ALL icons including tab bar — no install/plugin needed. Do NOT pull in `@expo/vector-icons`.

| Meaning | Lucide name |
|---------|-------------|
| Home | `Home` |
| Search | `Search` |
| Settings | `Settings` |
| Profile/User | `User` |
| Add/Create | `Plus` / `CirclePlus` |
| Cart | `ShoppingCart` |
| Heart/Favorite | `Heart` |
| Share | `Share2` |
| Camera | `Camera` |
| Notifications | `Bell` |
| Back | `ArrowLeft` |
| Forward/Next | `ChevronRight` |
| Close | `X` |
| Check | `CircleCheck` |
| Delete/Trash | `Trash2` |
| Edit | `Pencil` |
| Location | `MapPin` |
| Calendar | `Calendar` |
| Clock/Time | `Clock` |
| Star | `Star` |
| Download | `Download` |
| Upload | `Upload` |