import { DarkTheme, DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { useColorScheme, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { logout, useSignedIn } from "./src/auth/useSession";
import type { RootStack } from "./src/navigation";
import { AnalysisScreen } from "./src/screens/AnalysisScreen";
import { HistoryScreen } from "./src/screens/HistoryScreen";
import { LoginScreen } from "./src/screens/LoginScreen";
import { ProfileScreen } from "./src/screens/ProfileScreen";
import { RegisterScreen } from "./src/screens/RegisterScreen";
import { ResourceScreen } from "./src/screens/ResourceScreen";
import { UploadScreen } from "./src/screens/UploadScreen";
import { Button, Loading } from "./src/ui";

const Stack = createNativeStackNavigator<RootStack>();

/**
 * T-061/T-062: oturum yokken giriş/kayıt; varken CV yükleme, analiz ve sonuç, kaynak, geçmiş ve profil ekranları.
 * Oturum kapanınca (çıkış, hesap silme veya yenilenemeyen refresh token, src/auth/session.ts) ekran kendiliğinden
 * girişe döner.
 */
export default function App() {
  const signedIn = useSignedIn();
  const dark = useColorScheme() === "dark";

  return (
    <SafeAreaProvider>
      <NavigationContainer theme={dark ? DarkTheme : DefaultTheme}>
        {signedIn === undefined ? (
          <Loading label="Açılıyor" />
        ) : (
          <Stack.Navigator>
            {signedIn ? (
              <>
                <Stack.Screen
                  name="Upload"
                  component={UploadScreen}
                  options={({ navigation }) => ({
                    title: "Cv'ne Bakalım!",
                    headerRight: () => (
                      <View style={{ flexDirection: "row", gap: 12 }}>
                        <Button variant="link" title="Geçmiş" onPress={() => navigation.navigate("History")} />
                        <Button variant="link" title="Profil" onPress={() => navigation.navigate("Profile")} />
                      </View>
                    ),
                  })}
                />
                <Stack.Screen name="Analysis" component={AnalysisScreen} options={{ title: "Analiz" }} />
                <Stack.Screen name="Resource" component={ResourceScreen} options={{ title: "Kaynak" }} />
                <Stack.Screen name="History" component={HistoryScreen} options={{ title: "Geçmiş analizler" }} />
                <Stack.Screen
                  name="Profile"
                  component={ProfileScreen}
                  options={{
                    title: "Profil",
                    headerRight: () => <Button variant="link" title="Çıkış" onPress={() => void logout()} />,
                  }}
                />
              </>
            ) : (
              <>
                <Stack.Screen name="Login" component={LoginScreen} options={{ title: "Giriş yap" }} />
                <Stack.Screen name="Register" component={RegisterScreen} options={{ title: "Kayıt ol" }} />
              </>
            )}
          </Stack.Navigator>
        )}
      </NavigationContainer>
      <StatusBar style="auto" />
    </SafeAreaProvider>
  );
}
