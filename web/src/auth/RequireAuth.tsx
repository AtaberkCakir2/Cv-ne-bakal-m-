import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useSession } from "./useSession";

/** Oturum yoksa giriş ekranına gönderir; girişten sonra kullanıcı geldiği sayfaya döner (?sonra=). */
export function RequireAuth() {
  const session = useSession();
  const location = useLocation();
  if (!session) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/giris?sonra=${next}`} replace />;
  }
  return <Outlet />;
}
