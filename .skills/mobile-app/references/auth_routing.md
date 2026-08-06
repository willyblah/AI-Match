# Auth Routing Reference

## Stack.Protected Route Guard Structure

`src/app/_layout.tsx` (root layout):
```tsx
import { Stack } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { PortalHost } from "@rn-primitives/portal";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SessionProvider, useSession } from "@/ctx";
import "../global.css";

function RootLayoutNav() {
  const { session, isLoading } = useSession();

  if (isLoading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Protected guard={!session}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
      <Stack.Protected guard={!!session}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SessionProvider>
        <RootLayoutNav />
        <PortalHost />
      </SessionProvider>
    </GestureHandlerRootView>
  );
}
```

`src/app/index.tsx` — landing page component (inside `guard={!session}`, only visible when not logged in):
```tsx
import { Text, View } from "react-native";

export default function LandingScreen() {
  return (
    <View className="flex-1 items-center justify-center bg-background">
      <Text className="text-base text-foreground">Welcome to the app</Text>
    </View>
  );
}
```

## SessionProvider (ctx.tsx)

Pre-built in boilerplate — import directly, NEVER recreate:

```tsx
import { useSession } from "@/ctx";

const { session, isLoading } = useSession();
```

## Directory Structure

```
src/app/
  _layout.tsx          ← Root layout (GestureHandlerRootView + SessionProvider + Stack.Protected + PortalHost)
  index.tsx            ← Landing page component (in guard={!session}, removed when logged in)
  (app)/
    _layout.tsx        ← Stack navigator (guard={!!session})
    home.tsx           ← Main screen after login
    (tabs)/            ← Created when Tab navigation is needed
      _layout.tsx      ← Tabs navigator
      home.tsx         ← Home tab (NOT index.tsx — avoids URL collision with root index.tsx)
  (auth)/
    _layout.tsx        ← Stack navigator (guard={!session})
    sign-in.tsx        ← Sign-in screen
```