import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import type { components } from "./api/schema";

/**
 * Ekranlar. Oturum yokken sadece giriş/kayıt, varken sadece uygulama ekranları kayıtlıdır (App.tsx): oturum kapanınca
 * (çıkış, hesap silme ya da yenilenemeyen token) kullanıcı kendiliğinden giriş ekranına düşer, geri tuşuyla korumalı
 * ekrana dönemez.
 */
export type RootStack = {
  Login: { notice?: string } | undefined;
  Register: undefined;
  Upload: undefined;
  Analysis: { id: string };
  Resource: { resource: components["schemas"]["ResourceOut"]; skill: string; demand: string };
  History: undefined;
  Profile: undefined;
};

export type ScreenProps<K extends keyof RootStack> = NativeStackScreenProps<RootStack, K>;
