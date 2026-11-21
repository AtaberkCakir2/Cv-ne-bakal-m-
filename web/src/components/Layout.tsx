import { useQueryClient } from "@tanstack/react-query";
import { flushSync } from "react-dom";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { clearSession, currentRefreshToken, pendingRefresh } from "../auth/session";
import { useSession } from "../auth/useSession";
import { bugReportHref } from "../support";
import { ThemeToggle } from "../ui";

const LINKS = [
  { to: "/yukle", label: "CV yükle" },
  { to: "/gecmis", label: "Geçmiş" },
  { to: "/profil", label: "Profil" },
  { to: "/durum", label: "Durum" },
  { to: "/tasarim", label: "Tasarım" },
];

export function Layout() {
  const session = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  async function logout() {
    await pendingRefresh(); // yenileme sürerken eski token gönderilirse backend tüm oturumları kapatır
    const refresh_token = currentRefreshToken();
    // Sunucuya ulaşılamasa da bu cihazdaki oturum kapanır; refresh token en geç 7 günde zaten düşer.
    if (refresh_token) await api.POST("/api/v1/auth/logout", { body: { refresh_token } }).catch(() => undefined);
    // Önce giriş ekranına geç ve bunu hemen çiz (flushSync): korumalı sayfa hâlâ ekrandayken oturum silinirse
    // RequireAuth "?sonra=" ile yönlendirirdi ve sonraki girişte kullanıcı eski sayfaya dönerdi.
    flushSync(() => navigate("/giris"));
    clearSession();
    queryClient.clear(); // önceki kullanıcının verisi önbellekte kalmasın
  }

  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="brand">
          Cv'ne Bakalım!
        </NavLink>
        <nav>
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <ThemeToggle />
        {session ? (
          <button type="button" className="link-button" onClick={logout}>
            Çıkış
          </button>
        ) : (
          <NavLink to="/giris">Giriş</NavLink>
        )}
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="footer">
        <a href={bugReportHref(location.pathname)}>Hata bildir</a>
      </footer>
    </>
  );
}
