import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useId, useState, type FormEvent } from "react";
import { flushSync } from "react-dom";
import { useNavigate } from "react-router-dom";

import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import { CONSENT_NAMES, CONSENT_VERSION } from "../auth/consents";
import { clearSession, pendingRefresh } from "../auth/session";
import { Alert, Button, Card, Dialog, Spinner, TextField } from "../ui";

type Profile = components["schemas"]["ProfileOut"];
type Consent = components["schemas"]["ConsentOut"];

const MAX_NAME = 120;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" });
}

/**
 * Profil: hesap bilgileri ve hedef pozisyon, verileri indirme, onaylar ve hesap silme (KVKK md. 11).
 * docs/yasal metinleri "Profil → Verilerim" ve "Profil → Hesabını sil" yolunu anlatır; adlar onlarla aynı kalmalı.
 */
export function ProfilePage() {
  const me = useQuery({ queryKey: ["me"], queryFn: async () => unwrap(await api.GET("/api/v1/users/me")) });

  return (
    <div className="stack profile">
      <h1>Profil</h1>
      {me.isPending && <Spinner />}
      {me.isError && <Alert tone="error">{problemMessage(me.error)}</Alert>}
      {me.data && <AccountCard profile={me.data} />}
      <MyDataCard />
      <DeleteAccountCard />
    </div>
  );
}

function AccountCard({ profile }: { profile: Profile }) {
  const queryClient = useQueryClient();
  const ids = { name: useId(), role: useId() };
  const roles = useQuery({ queryKey: ["roles"], queryFn: async () => unwrap(await api.GET("/api/v1/roles")) });
  const [name, setName] = useState(profile.full_name ?? "");
  const [roleId, setRoleId] = useState(profile.target_role?.id);
  const [saved, setSaved] = useState(false);

  const save = useMutation({
    mutationFn: async () =>
      unwrap(
        await api.PATCH("/api/v1/users/me", {
          // Pozisyon sadece değiştiyse gönderilir: profildeki pozisyon artık aktif değilse ad kaydı 422 almasın.
          body: {
            full_name: name.trim() || null,
            ...(roleId !== profile.target_role?.id && { target_role_id: roleId ?? null }),
          },
        }),
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data);
      setSaved(true);
    },
  });

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaved(false);
    save.mutate();
  }

  return (
    <Card title="Hesap bilgileri">
      <dl className="details profile__facts">
        <dt>E-posta</dt>
        <dd>{profile.email}</dd>
        <dt>E-posta doğrulandı mı?</dt>
        <dd>{profile.is_verified ? "Evet" : "Hayır, e-postandaki bağlantıyı aç."}</dd>
      </dl>
      <form onSubmit={submit} noValidate>
        {save.isError && <Alert tone="error">{problemMessage(save.error)}</Alert>}
        <TextField
          id={ids.name}
          label="Ad soyad (isteğe bağlı)"
          autoComplete="name"
          maxLength={MAX_NAME}
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setSaved(false);
          }}
        />
        <div className="field">
          <label className="field__label" htmlFor={ids.role}>
            Hedef pozisyon
          </label>
          <select
            id={ids.role}
            className="field__input"
            value={roles.data?.some((r) => r.id === roleId) ? roleId : ""}
            onChange={(e) => {
              setRoleId(e.target.value ? Number(e.target.value) : undefined);
              setSaved(false);
            }}
            disabled={roles.isPending}
          >
            <option value="">Seçilmedi</option>
            {roles.data?.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <span className="field__hint">CV yüklerken bu pozisyon hazır seçili gelir.</span>
        </div>
        <div className="row">
          <Button type="submit" loading={save.isPending}>
            Kaydet
          </Button>
          <span role="status">{saved && "Kaydedildi."}</span>
        </div>
      </form>
    </Card>
  );
}

function MyDataCard() {
  const queryClient = useQueryClient();
  const consents = useQuery({
    queryKey: ["consents"],
    queryFn: async () => unwrap(await api.GET("/api/v1/users/me/consents")),
  });
  const [exportError, setExportError] = useState<string>();
  const [exporting, setExporting] = useState(false);
  const [confirmWithdraw, setConfirmWithdraw] = useState(false);
  const [notice, setNotice] = useState<string>();

  // Her tür için en son kayıt yürürlüktedir; eski sürüm satırları silinmez (backend sürümlü tutar).
  const latest = new Map<string, Consent>();
  for (const c of consents.data ?? []) {
    const prev = latest.get(c.consent_type);
    if (!prev || Date.parse(c.accepted_at) >= Date.parse(prev.accepted_at)) latest.set(c.consent_type, c);
  }
  const explicit = latest.get("acik_riza");
  const explicitActive = explicit != null && explicit.withdrawn_at == null;

  const change = useMutation({
    onMutate: () => setNotice(undefined),
    mutationFn: async (give: boolean) =>
      give
        ? unwrap(
            await api.POST("/api/v1/users/me/consents", {
              body: { consents: [{ consent_type: "acik_riza", version: CONSENT_VERSION }] },
            }),
          )
        : unwrap(
            await api.DELETE("/api/v1/users/me/consents/{consent_type}", {
              params: { path: { consent_type: "acik_riza" } },
            }),
          ),
    onSuccess: (data, give) => {
      queryClient.setQueryData(["consents"], data);
      setConfirmWithdraw(false);
      setNotice(give ? "Açık rızan kaydedildi; yeniden analiz başlatabilirsin." : "Açık rızan geri alındı.");
    },
  });

  async function download() {
    setExportError(undefined);
    setExporting(true);
    try {
      const data = unwrap(await api.GET("/api/v1/users/me/export"));
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `careerai-verilerim-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 0); // indirme başlamadan adres iptal olmasın
    } catch (e) {
      setExportError(problemMessage(e));
    } finally {
      setExporting(false);
    }
  }

  return (
    <Card title="Verilerim">
      <p className="muted">
        Hesabın, analizlerin ve onay kayıtların tek bir JSON dosyasında iner. CV dosyan saklanmadığı için dosyada yer
        almaz.
      </p>
      {exportError && <Alert tone="error">{exportError}</Alert>}
      <Button variant="secondary" loading={exporting} onClick={download}>
        Verilerimi indir
      </Button>

      <h3 className="profile__subtitle">Onaylarım</h3>
      {consents.isPending && <Spinner />}
      {consents.isError && <Alert tone="error">{problemMessage(consents.error)}</Alert>}
      {consents.data && (
        <ul className="profile__consents">
          {[...latest.values()].map((c) => (
            <li key={c.consent_type}>
              <strong>{CONSENT_NAMES[c.consent_type]}</strong>
              <span className="muted">
                {" "}
                · sürüm {c.version} · {formatDate(c.accepted_at)}
                {c.withdrawn_at && ` · ${formatDate(c.withdrawn_at)} tarihinde geri alındı`}
              </span>
            </li>
          ))}
        </ul>
      )}
      <div role="status">{notice && <p>{notice}</p>}</div>
      {change.isError && !confirmWithdraw && <Alert tone="error">{problemMessage(change.error)}</Alert>}
      {consents.data &&
        (explicitActive ? (
          <Button variant="secondary" onClick={() => setConfirmWithdraw(true)}>
            Açık rızamı geri al
          </Button>
        ) : (
          <>
            <p className="muted profile__note">
              Açık rıza metninin {CONSENT_VERSION} sürümünü onaylamış olursun; CV'ndeki yetkinlikler analiz için işlenir.
            </p>
            <Button loading={change.isPending} onClick={() => change.mutate(true)}>
              Açık rıza ver
            </Button>
          </>
        ))}
      <p className="muted profile__note">
        Aydınlatma metni ve kullanım koşulları hizmetin kendisi için gerekli; onlardan çıkmak için hesabını silebilirsin.
      </p>

      <Dialog open={confirmWithdraw} title="Açık rızan geri alınsın mı?" onClose={() => setConfirmWithdraw(false)}>
        <p>
          Geri alırsan yeni CV analizi başlatamazsın. Önceki analizlerin silinmez; istersen Geçmiş sayfasından
          silebilirsin. Rızanı daha sonra bu sayfadan yeniden verebilirsin.
        </p>
        {change.isError && <Alert tone="error">{problemMessage(change.error)}</Alert>}
        <div className="row">
          <Button variant="danger" loading={change.isPending} onClick={() => change.mutate(false)}>
            Geri al
          </Button>
          <Button variant="secondary" onClick={() => setConfirmWithdraw(false)}>
            Vazgeç
          </Button>
        </div>
      </Dialog>
    </Card>
  );
}

function DeleteAccountCard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const passwordId = useId();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);
  // showModal açılışta odağı zaten ilk alana (şifre) verir; hatadan sonra yine oraya dönülür.
  const focusPassword = () => document.getElementById(passwordId)?.focus();

  function close() {
    setOpen(false);
    setPassword("");
    setError(undefined);
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (pending) return;
    if (!password) {
      setError("Onaylamak için şifreni gir.");
      focusPassword();
      return;
    }
    setError(undefined);
    setPending(true);
    try {
      const { error: problem, response } = await api.DELETE("/api/v1/users/me", { body: { password } });
      if (!response.ok) {
        setError(problemMessage(problem));
        focusPassword();
        return;
      }
      await pendingRefresh(); // süren bir yenileme, silinen oturumu temizlendikten sonra geri yazmasın
      // Backend tüm oturumları kapattı. Korumalı sayfa ekrandayken oturum silinirse RequireAuth "?sonra=/profil" ile
      // yönlendirirdi: önce giriş ekranına geç (flushSync), sonra yerel oturumu ve önbelleği temizle.
      flushSync(() =>
        navigate("/giris", {
          replace: true,
          state: { notice: "Hesabın kapatıldı. Verilerin 30 gün içinde kalıcı olarak silinecek." },
        }),
      );
      clearSession();
      queryClient.clear();
    } catch {
      setError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card title="Hesabını sil">
      <p>
        Hesabın hemen kapatılır, tüm oturumların sonlanır ve kişisel bilgilerin anonimleştirilir. Hesap bilgilerin,
        analizlerin ve onay kayıtların 30 gün sonra kalıcı olarak silinir. Bu işlem geri alınamaz; istersen önce
        verilerini indir.
      </p>
      <Button variant="danger" onClick={() => setOpen(true)}>
        Hesabımı sil
      </Button>

      <Dialog open={open} title="Hesabın silinsin mi?" onClose={close}>
        <form onSubmit={submit} noValidate>
          <p>Onaylamak için şifreni gir. Bu işlem geri alınamaz.</p>
          {error && <Alert tone="error">{error}</Alert>}
          <TextField
            id={passwordId}
            label="Şifre"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="row">
            <Button type="submit" variant="danger" loading={pending}>
              Hesabımı kalıcı olarak sil
            </Button>
            <Button variant="secondary" onClick={close}>
              Vazgeç
            </Button>
          </div>
        </form>
      </Dialog>
    </Card>
  );
}
