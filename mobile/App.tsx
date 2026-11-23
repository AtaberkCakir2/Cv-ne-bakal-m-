import { DarkTheme, DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { useColorScheme } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { logout, useSignedIn } from "./src/auth/useSession";
import type { RootStack } from "./src/navigation";
import { AnalysisScreen } from "./src/screens/AnalysisScreen";
import { LoginScreen } from "./src/screens/LoginScreen";
import { RegisterScreen } from "./src/screens/RegisterScreen";
import { UploadScreen } from "./src/screens/UploadScreen";
import { Button, Loading } from "./src/ui";

const Stack = createNativeStackNavigator<RootStack>();

/**
 * T-061: oturum yokken giriş/kayıt, varken CV yükleme ve analiz ekranları. Oturum kapanınca (çıkış veya yenilenemeyen
 * refresh token, src/auth/session.ts) ekran kendiliğinden girişe döner.
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
                  options={{
                    title: "Cv'ne Bakalım!",
                    headerRight: () => <Button variant="link" title="Çıkış" onPress={() => void logout()} />,
                  }}
                />
                <Stack.Screen name="Analysis" component={AnalysisScreen} options={{ title: "Analiz" }} />
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
