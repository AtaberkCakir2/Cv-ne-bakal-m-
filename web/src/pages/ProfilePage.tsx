import { useQuery } from "@tanstack/react-query";

import { api, problemMessage, unwrap } from "../api/client";
import { Alert, Card, Spinner } from "../ui";

/** Şimdilik hesap bilgisi; KVKK işlemleri (veri indirme, hesap silme) T-049 ile gelecek. */
export function ProfilePage() {
  const me = useQuery({ queryKey: ["me"], queryFn: async () => unwrap(await api.GET("/api/v1/users/me")) });

  return (
    <Card title="Profil" headingLevel={1}>
      {me.isPending && <Spinner />}
      {me.isError && <Alert tone="error">{problemMessage(me.error)}</Alert>}
      {me.data && (
        <dl className="details">
          <dt>E-posta</dt>
          <dd>{me.data.email}</dd>
          <dt>Ad soyad</dt>
          <dd>{me.data.full_name ?? "—"}</dd>
          <dt>E-posta doğrulandı mı?</dt>
          <dd>{me.data.is_verified ? "Evet" : "Hayır, e-postandaki bağlantıyı aç."}</dd>
        </dl>
      )}
    </Card>
  );
}
