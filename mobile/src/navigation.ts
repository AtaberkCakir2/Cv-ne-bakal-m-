import type { NativeStackScreenProps } from "@react-navigation/native-stack";

/**
 * Ekranlar. Oturum yokken sadece giriş/kayıt, varken sadece uygulama ekranları kayıtlıdır (App.tsx): oturum kapanınca
 * (çıkış ya da yenilenemeyen token) kullanıcı kendiliğinden giriş ekranına düşer, geri tuşuyla korumalı ekrana dönemez.
 */
export type RootStack = {
  Login: { notice?: string } | undefined;
  Register: undefined;
  Upload: undefined;
  Analysis: { id: string };
};

export type ScreenProps<K extends keyof RootStack> = NativeStackScreenProps<RootStack, K>;
