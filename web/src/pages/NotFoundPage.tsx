import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section>
      <h1>Sayfa bulunamadı</h1>
      <p>
        <Link to="/">Ana sayfaya dön</Link>
      </p>
    </section>
  );
}
