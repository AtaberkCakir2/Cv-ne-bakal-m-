import { Platform } from "react-native";

/**
 * API adresi derleme anında `EXPO_PUBLIC_API_URL` ile gelir (eas.json profilleri veya mobile/.env.local, commit'lenmez).
 * Verilmezse geliştirme varsayılanı: Android emülatörü bilgisayarın kendisine 10.0.2.2 ile ulaşır, iOS simülatörü
 * ve web 127.0.0.1 ile. Gerçek telefonda bilgisayarın yerel ağ adresi verilmelidir (ör. http://192.168.1.20:8000).
 */
const fallback = Platform.OS === "android" ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000";

export const API_URL: string = (process.env.EXPO_PUBLIC_API_URL || fallback).replace(/\/+$/, "");

/** KVKK ve kullanım metinlerinin yayınlandığı site (Cloudflare Pages, T-065/T-070); uygulama bunları tarayıcıda açar. */
export const LEGAL_URL = "https://cvnebakalim.com";
