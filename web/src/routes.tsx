import { createBrowserRouter } from "react-router-dom";

import { RequireAuth } from "./auth/RequireAuth";
import { Layout } from "./components/Layout";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { ResetPasswordPage } from "./pages/auth/ResetPasswordPage";
import { VerifyEmailPage } from "./pages/auth/VerifyEmailPage";
import { DesignSystemPage } from "./pages/DesignSystemPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ProfilePage } from "./pages/ProfilePage";
import { StatusPage } from "./pages/StatusPage";

/**
 * Ekranlar web/prototip (T-021 wireframe) ile aynı adları kullanır. E-posta bağlantılarının yolları
 * (/e-posta-dogrula, /sifre-sifirla) backend ile aynı olmalı (backend/app/services/auth.py).
 * Electron (file://) için createHashRouter'a geçmek yeterli olacak.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <PlaceholderPage title="CareerAI" note="CV'ni hedef pozisyonla karşılaştır." /> },
      { path: "giris", element: <LoginPage /> },
      { path: "kayit", element: <RegisterPage /> },
      { path: "sifremi-unuttum", element: <ForgotPasswordPage /> },
      { path: "sifre-sifirla", element: <ResetPasswordPage /> },
      { path: "e-posta-dogrula", element: <VerifyEmailPage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: "pozisyon", element: <PlaceholderPage title="Hedef pozisyon" /> },
          { path: "yukle", element: <PlaceholderPage title="CV yükle" note="Sadece PDF, en fazla 10 MB." /> },
          { path: "analiz/:id", element: <PlaceholderPage title="Analiz sonucu" /> },
          { path: "gecmis", element: <PlaceholderPage title="Geçmiş analizler" /> },
          { path: "profil", element: <ProfilePage /> },
        ],
      },
      { path: "durum", element: <StatusPage /> },
      { path: "tasarim", element: <DesignSystemPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
