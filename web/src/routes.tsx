import { createBrowserRouter } from "react-router-dom";

import { Layout } from "./components/Layout";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { StatusPage } from "./pages/StatusPage";

/**
 * Ekranlar web/prototip (T-021 wireframe) ile aynı adları kullanır. Sayfalar şimdilik yer tutucu;
 * içerikleri T-041 ve sonrasında gelir. Electron (file://) için createHashRouter'a geçmek yeterli olacak.
 */
export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <PlaceholderPage title="CareerAI" note="CV'ni hedef pozisyonla karşılaştır." /> },
      { path: "giris", element: <PlaceholderPage title="Giriş" /> },
      { path: "kayit", element: <PlaceholderPage title="Kayıt" note="KVKK onayları kayıtla birlikte alınır." /> },
      { path: "pozisyon", element: <PlaceholderPage title="Hedef pozisyon" /> },
      { path: "yukle", element: <PlaceholderPage title="CV yükle" note="Sadece PDF, en fazla 10 MB." /> },
      { path: "analiz/:id", element: <PlaceholderPage title="Analiz sonucu" /> },
      { path: "gecmis", element: <PlaceholderPage title="Geçmiş analizler" /> },
      { path: "profil", element: <PlaceholderPage title="Profil" /> },
      { path: "durum", element: <StatusPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
