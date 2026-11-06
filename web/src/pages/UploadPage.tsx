import { useQuery } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState, type DragEvent, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { cvFileError, formatSize, formatWait, MAX_CV_PAGES } from "../analysis/cvFile";
import { api, problemMessage, unwrap, type Problem } from "../api/client";
import { focusFirstError } from "../auth/validation";
import { Alert, Button, Card, Spinner } from "../ui";

/** İlan sayısı bunun altındaysa oranlar daha az güvenilir (risk R-11, prototip). */
const LOW_DATA_POSTINGS = 50;
/** 5 MB yavaş bağlantıda da bu sürede gider; sunucu yanıt vermezse düğme sonsuza dek "İşleniyor" kalmasın. */
const UPLOAD_TIMEOUT_MS = 60_000;

/** T-052: hedef pozisyon seçimi + CV yükleme. Başarılı yüklemede bekleme ekranına (/analiz/:id) geçilir. */
export function UploadPage() {
  const navigate = useNavigate();
  const chooseSeq = useRef(0);
  const ids = { role: useId(), file: useId(), rules: useId(), data: useId() };

  const roles = useQuery({ queryKey: ["roles"], queryFn: async () => unwrap(await api.GET("/api/v1/roles")) });
  const me = useQuery({ queryKey: ["me"], queryFn: async () => unwrap(await api.GET("/api/v1/users/me")) });
  const [chosenRole, setChosenRole] = useState<number>();
  // Kullanıcı seçmediyse profildeki hedef pozisyon (hâlâ aktifse), o da yoksa boş ("Seç…").
  const profileRole = me.data?.target_role?.id;
  const roleId = chosenRole ?? (roles.data?.some((r) => r.id === profileRole) ? profileRole : undefined);
  const role = roles.data?.find((r) => r.id === roleId);

  const stats = useQuery({
    queryKey: ["role-skills", role?.slug, 1],
    enabled: Boolean(role),
    queryFn: async () =>
      unwrap(
        await api.GET("/api/v1/roles/{slug}/skills", { params: { path: { slug: role!.slug }, query: { limit: 1 } } }),
      ),
  });

  const [file, setFile] = useState<File>();
  const [fileError, setFileError] = useState<string>();
  const [roleError, setRoleError] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [dragging, setDragging] = useState(false);
  const [pending, setPending] = useState(false);

  // Bölge dışına bırakılan dosyayı tarayıcı açıp sayfadan çıkmasın.
  useEffect(() => {
    const stop = (e: globalThis.DragEvent) => e.preventDefault();
    window.addEventListener("dragover", stop);
    window.addEventListener("drop", stop);
    return () => {
      window.removeEventListener("dragover", stop);
      window.removeEventListener("drop", stop);
    };
  }, []);

  async function choose(candidate: File | undefined) {
    setFormError(undefined);
    if (!candidate) return;
    // Arka arkaya iki seçimde sonuncusu geçerli: önceki kontrol geç biterse yok sayılır.
    const attempt = ++chooseSeq.current;
    let error: string | undefined;
    try {
      error = await cvFileError(candidate);
    } catch {
      error = "Dosya okunamadı. Tekrar seç.";
    }
    if (attempt !== chooseSeq.current) return;
    setFileError(error);
    setFile(error ? undefined : candidate);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (pending) return;
    if (e.dataTransfer.files.length > 1) {
      setFormError(undefined);
      setFileError("Tek bir PDF dosyası bırak.");
      return;
    }
    void choose(e.dataTransfer.files[0]);
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setFormError(undefined);
    setRoleError(roleId ? undefined : "Hedef pozisyonu seç.");
    if (!file) setFileError((current) => current ?? "CV dosyanı seç.");
    if (!roleId || !file) {
      requestAnimationFrame(() => focusFirstError(form));
      return;
    }
    setPending(true);
    try {
      const { data, error, response } = await api.POST("/api/v1/analyses", {
        signal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS),
        // openapi tipi dosyayı string (binary) sayar; gövde FormData olarak gönderilir.
        body: { file: file as unknown as string, target_role_id: roleId },
        bodySerializer: (body) => {
          const form = new FormData();
          form.append("file", file, file.name);
          form.append("target_role_id", String(body.target_role_id));
          return form;
        },
      });
      if (data) {
        navigate(`/analiz/${data.analysis_id}`);
        return;
      }
      setFormError(uploadErrorMessage(error, response));
    } catch (err) {
      setFormError(
        err instanceof DOMException && err.name === "TimeoutError"
          ? "Yükleme zaman aşımına uğradı. Bağlantını kontrol edip tekrar dene."
          : "Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.",
      );
    } finally {
      setPending(false);
    }
  }

  if (roles.isPending || me.isPending) return <Spinner label="Yükleniyor" />;
  if (roles.isError) return <Alert tone="error">{problemMessage(roles.error)}</Alert>;

  const total = stats.data?.total_postings;
  const lowData = Boolean(role) && total !== undefined && total < LOW_DATA_POSTINGS;
  return (
    <Card title="CV'ni yükle" headingLevel={1} className="upload-card">
      <p className="muted">CV'n seçtiğin pozisyonun güncel ilanlarıyla karşılaştırılır.</p>
      {formError && <Alert tone="error">{formError}</Alert>}
      <form onSubmit={submit} noValidate>
        <div className="field">
          <label className="field__label" htmlFor={ids.role}>
            Hedef pozisyon
          </label>
          <select
            id={ids.role}
            className="field__input"
            value={roleId ?? ""}
            onChange={(e) => {
              setChosenRole(Number(e.target.value) || undefined);
              setRoleError(undefined);
            }}
            aria-invalid={roleError ? true : undefined}
            aria-describedby={[roleError && `${ids.role}-error`, lowData && ids.data].filter(Boolean).join(" ") || undefined}
            disabled={pending}
            required
          >
            <option value="">Seç…</option>
            {roles.data.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          {roleError && (
            <span id={`${ids.role}-error`} className="field__error">
              {roleError}
            </span>
          )}
          {lowData && (
            <span id={ids.data} className="field__hint">
              {total === 0
                ? "Bu pozisyon için henüz güncel ilan yok; sonuçta talep oranları boş görünebilir."
                : `Bu pozisyon için sadece ${total} güncel ilan var; oranlar daha az güvenilir.`}
            </span>
          )}
        </div>

        <div
          className={["drop", dragging && "drop--over", fileError && "drop--error"].filter(Boolean).join(" ")}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(e) => {
            // Alt öğelerin üzerine geçerken de tetiklenir; sadece bölgeden gerçekten çıkınca vurgu kalksın.
            if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false);
          }}
          onDrop={onDrop}
        >
          {/* Seçilen dosya ekran okuyucuya da duyurulsun. */}
          <p className={file ? "drop__file" : "drop__title"} role="status">
            {file ? (
              <>
                <strong>{file.name}</strong>
                <span className="muted"> · {formatSize(file.size)}</span>
              </>
            ) : (
              "PDF dosyanı buraya sürükle"
            )}
          </p>
          <input
            id={ids.file}
            disabled={pending}
            className="visually-hidden"
            type="file"
            accept="application/pdf,.pdf"
            aria-describedby={[ids.rules, fileError && `${ids.file}-error`].filter(Boolean).join(" ")}
            aria-invalid={fileError ? true : undefined}
            onChange={(e) => {
              void choose(e.target.files?.[0]);
              e.target.value = ""; // aynı dosya tekrar seçilebilsin
            }}
          />
          <label htmlFor={ids.file} className="btn btn--secondary">
            {file ? "Başka dosya seç" : "Dosya seç"}
          </label>
          <p id={ids.rules} className="field__hint">
            Sadece PDF · en fazla 5 MB ve {MAX_CV_PAGES} sayfa · Türkçe veya İngilizce
          </p>
          {fileError && (
            <p id={`${ids.file}-error`} className="field__error" role="alert">
              {fileError}
            </p>
          )}
        </div>

        <Button type="submit" block loading={pending}>
          Analizi başlat
        </Button>
      </form>
      <Alert tone="info">CV dosyan saklanmaz; analizden sonra sadece çıkan yetkinlikler hesabında kalır.</Alert>
    </Card>
  );
}

function uploadErrorMessage(error: unknown, response: Response): string {
  const problem = error as Partial<Problem> | undefined;
  const wait = Number(response.headers.get("Retry-After"));
  if (response.status === 429) {
    return `Saatte en fazla 5 analiz yapabilirsin.${wait > 0 ? ` ${formatWait(wait)} sonra tekrar dene.` : ""}`;
  }
  if (response.status === 503) {
    return `Sistem şu an yoğun, analiz başlatılamadı.${wait > 0 ? ` ${formatWait(wait)} sonra tekrar dene.` : ""}`;
  }
  if (problem?.code === "PDF_TOO_LARGE") return `Dosya 5 MB veya ${MAX_CV_PAGES} sayfadan büyük olamaz.`;
  if (problem?.code === "PDF_UNREADABLE") return "PDF okunamadı. Dosya bozuk ya da şifreli olabilir.";
  return problemMessage(error);
}
