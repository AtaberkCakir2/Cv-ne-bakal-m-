import { NavLink, Outlet } from "react-router-dom";

const LINKS = [
  { to: "/yukle", label: "CV yükle" },
  { to: "/gecmis", label: "Geçmiş" },
  { to: "/profil", label: "Profil" },
  { to: "/durum", label: "Durum" },
];

export function Layout() {
  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="brand">
          CareerAI
        </NavLink>
        <nav>
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to}>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <NavLink to="/giris">Giriş</NavLink>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </>
  );
}
