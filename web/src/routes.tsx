import { createBrowserRouter } from "react-router-dom";

import { RequireAuth } from "./auth/RequireAuth";
import { Layout } from "./components/Layout";
import { AnalysisPage } from "./pages/AnalysisPage";
import { ForgotPasswordPage } from "./pages/auth/ForgotPasswordPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { ResetPasswordPage } from "./pages/auth/ResetPasswordPage";
import { VerifyEmailPage } from "./pages/auth/VerifyEmailPage";
import { DesignSystemPage } from "./pages/DesignSystemPage";
import { HistoryPage } from "./pages/HistoryPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ProfilePage } from "./pages/ProfilePage";
import { StatusPage } from "./pages/StatusPage";
import { UploadPage } from "./pages/UploadPage";

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
      { index: true, element: <PlaceholderPage title="Cv'ne Bakalım!" note="CV'ni hedef pozisyonla karşılaştır." /> },
      { path: "giris", element: <LoginPage /> },
      { path: "kayit", element: <RegisterPage /> },
      { path: "sifremi-unuttum", element: <ForgotPasswordPage /> },
      { path: "sifre-sifirla", element: <ResetPasswordPage /> },
      { path: "e-posta-dogrula", element: <VerifyEmailPage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: "pozisyon", element: <PlaceholderPage title="Hedef pozisyon" /> },
          { path: "yukle", element: <UploadPage /> },
          { path: "analiz/:id", element: <AnalysisPage /> },
          { path: "gecmis", element: <HistoryPage /> },
          { path: "profil", element: <ProfilePage /> },
        ],
      },
      { path: "durum", element: <StatusPage /> },
      { path: "tasarim", element: <DesignSystemPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
