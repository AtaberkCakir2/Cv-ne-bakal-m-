import { useState } from "react";
import { Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import { Alert, Body, Button, Chip, Field, RatioBar, Section, Title } from "../ui";
import { useColors } from "../ui/theme";
import { demandText, formatDate, LEVEL, LOW_DATA_POSTINGS, percentOf, PROVIDER, resourceMeta } from "./format";

type Analysis = components["schemas"]["AnalysisOut"];
type Resource = components["schemas"]["ResourceOut"];

const MAX_COMMENT = 1000;

/**
 * T-062: tamamlanmış analizin sonuç panosu (web/src/analysis/ResultDashboard.tsx ile aynı içerik): uyum puanı, CV'de
 * bulunanlar, talep oranlarıyla eksikler, eksik başına kaynaklar (dokununca kaynak detayı), geri bildirim, kaynak atfı.
 */
export function ResultView({
  data,
  onOpenResource,
  onAgain,
}: {
  data: Analysis;
  onOpenResource: (resource: Resource, skill: string, demand: string) => void;
  onAgain: () => void;
}) {
  const c = useColors();
  const present = data.present_skills ?? [];
  const missing = [...(data.missing_skills ?? [])].sort((a, b) => a.priority - b.priority);
  const postings = data.postings_analyzed;
  const hasYoutube = missing.some((m) => m.resources.some((r) => r.provider === "youtube"));
  const score = data.match_score;

  return (
    <>
      <View style={styles.head}>
        {score != null && (
          <View
            accessible
            accessibilityLabel={`Uyum puanı 100 üzerinden ${Math.round(score)}`}
            style={[styles.score, { borderColor: c.primary }]}
          >
            <Text style={[styles.scoreText, { color: c.primary }]}>{Math.round(score)}</Text>
            <Text style={{ color: c.muted, fontSize: 12 }}>/ 100</Text>
          </View>
        )}
        <View style={{ flex: 1, gap: 4 }}>
          <Title>{score != null ? `${data.target_role.name} için uyumun` : `${data.target_role.name} analizi`}</Title>
          <Body muted>
            {postings != null ? `${postings} güncel ilanla karşılaştırıldı · ` : ""}
            {formatDate(data.completed_at ?? data.created_at)}
          </Body>
        </View>
      </View>

      {postings != null && postings < LOW_DATA_POSTINGS && (
        <Alert tone="warning">Bu pozisyon için sadece {postings} güncel ilan var; oranlar daha az güvenilir.</Alert>
      )}

      <Section title={`CV'nde bulunanlar (${present.length})`}>
        {present.length ? (
          <View style={styles.chips}>
            {present.map((s) => (
              <Chip key={s.skill} label={s.skill} meta={s.verified === false ? `${LEVEL[s.level]} · tahmini` : LEVEL[s.level]} />
            ))}
          </View>
        ) : (
          <Body muted>CV'nde bu pozisyonla ilgili yetkinlik bulunamadı.</Body>
        )}
        {present.some((s) => s.verified === false) && (
          <Body muted>"Tahmini" yetkinlikler taksonomide yok; yapay zekânın çıkarımıdır.</Body>
        )}
      </Section>

      <Section title={`Eksik yetkinlikler (${missing.length})`}>
        {missing.length ? (
          <>
            <Body muted>Önem sırasına göre; çubuk, bu yetkinliği isteyen ilanların oranı. Kaynağa dokun, ayrıntısını gör.</Body>
            {missing.map((m) => {
              const demand = demandText(m.demand_ratio, postings);
              return (
                <View key={m.skill} style={styles.gap}>
                  <Text style={[styles.gapTitle, { color: c.text }]}>
                    {m.priority}. {m.skill}
                  </Text>
                  <RatioBar ratio={m.demand_ratio} label={`${m.skill}: ilanların ${percentOf(m.demand_ratio)} istiyor`} />
                  <Text style={{ color: c.muted }}>{demand}</Text>
                  {m.resources.length ? (
                    m.resources.map((r) => (
                      <Pressable
                        key={r.resource_id}
                        accessibilityRole="button"
                        accessibilityHint="Kaynak ayrıntısını açar"
                        onPress={() => onOpenResource(r, m.skill, demand)}
                        style={({ pressed }) => [
                          styles.resource,
                          { borderColor: c.border, backgroundColor: c.bg },
                          pressed && { opacity: 0.7 },
                        ]}
                      >
                        <Text style={{ color: c.muted, fontSize: 12 }}>{PROVIDER[r.provider]}</Text>
                        <Text style={{ color: c.text, fontWeight: "600" }}>{r.title}</Text>
                        <Text style={{ color: c.muted, fontSize: 12 }}>{resourceMeta(r)}</Text>
                      </Pressable>
                    ))
                  ) : (
                    <Body muted>Bu yetkinlik için henüz önerilecek kaynak yok.</Body>
                  )}
                </View>
              );
            })}
          </>
        ) : (
          <Body muted>Bu pozisyonun öne çıkan yetkinliklerinin hepsi CV'nde var.</Body>
        )}
      </Section>

      <FeedbackSection analysisId={data.analysis_id} saved={data.feedback ?? undefined} />
      <Button title="Yeni analiz başlat" onPress={onAgain} />
      <SourceAttribution youtube={hasYoutube} />
    </>
  );
}

function FeedbackSection({ analysisId, saved }: { analysisId: string; saved?: { rating: number; comment?: string | null } }) {
  const c = useColors();
  const [rating, setRating] = useState<number | undefined>(saved?.rating);
  const [comment, setComment] = useState(saved?.comment ?? "");
  const [error, setError] = useState<string>();
  const [editing, setEditing] = useState(!saved);
  const [pending, setPending] = useState(false);

  async function submit() {
    setError(undefined);
    if (!rating) {
      setError("Puan için 1 ile 5 arasında bir yıldız seç.");
      return;
    }
    setPending(true);
    try {
      unwrap(
        await api.POST("/api/v1/analyses/{analysis_id}/feedback", {
          params: { path: { analysis_id: analysisId } },
          body: { rating, comment: comment.trim() || null },
        }),
      );
      setEditing(false);
    } catch (e) {
      setError(problemMessage(e));
    } finally {
      setPending(false);
    }
  }

  return (
    <Section title="Bu analiz işine yaradı mı?">
      {!editing ? (
        <>
          <Text accessibilityLiveRegion="polite" style={{ color: c.text }}>
            Teşekkürler, geri bildirimin kaydedildi ({rating} / 5).
          </Text>
          <Button variant="secondary" title="Değiştir" onPress={() => setEditing(true)} />
        </>
      ) : (
        <>
          {error && <Alert tone="error">{error}</Alert>}
          <View accessibilityRole="radiogroup" accessibilityLabel="Puanın" style={styles.stars}>
            {[1, 2, 3, 4, 5].map((n) => (
              <Pressable
                key={n}
                accessibilityRole="radio"
                accessibilityLabel={`${n} yıldız`}
                accessibilityState={{ selected: rating === n, disabled: pending }}
                disabled={pending}
                onPress={() => setRating(n)}
                style={styles.star}
              >
                <Text style={{ fontSize: 30, color: rating && n <= rating ? c.warning : c.border }}>★</Text>
              </Pressable>
            ))}
          </View>
          <Field
            label="Yorum (isteğe bağlı)"
            hint="Kişisel bilgi yazma; yorumun sadece ürünü geliştirmek için okunur."
            value={comment}
            onChangeText={setComment}
            maxLength={MAX_COMMENT}
            multiline
            style={{ minHeight: 80, textAlignVertical: "top", paddingTop: 10 }}
            editable={!pending}
          />
          <Button title="Gönder" onPress={() => void submit()} loading={pending} />
        </>
      )}
    </Section>
  );
}

/**
 * İlan sayısı gösterilen her yerde zorunlu kaynak atfı (scraper/kaynak-uygunluk.md kural 7; web'deki
 * SourceAttribution ile aynı liste). YouTube önerildiyse YouTube API şartları bağlantıları.
 */
const SOURCES = [
  { name: "Remotive", url: "https://remotive.com" },
  { name: "Himalayas", url: "https://himalayas.app" },
  { name: "Remote OK", url: "https://remoteok.com" },
  { name: "Hacker News", url: "https://news.ycombinator.com" },
  { name: "Arbeitnow", url: "https://www.arbeitnow.com" },
  { name: "Jobicy", url: "https://jobicy.com" },
];
const YOUTUBE_LINKS = [
  { name: "YouTube Hizmet Şartları", url: "https://www.youtube.com/t/terms" },
  { name: "Google Gizlilik Politikası", url: "https://policies.google.com/privacy" },
];

function SourceAttribution({ youtube }: { youtube: boolean }) {
  const c = useColors();
  const link = (l: { name: string; url: string }) => (
    <Text key={l.name} accessibilityRole="link" style={{ color: c.primary }} onPress={() => void Linking.openURL(l.url)}>
      {l.name}
    </Text>
  );
  const join = (list: { name: string; url: string }[], sep: string) =>
    list.flatMap((l, i) => (i ? [sep, link(l)] : [link(l)]));
  return (
    <View style={styles.attribution}>
      <Text style={{ color: c.muted, fontSize: 12 }}>İlan verileri: {join(SOURCES, ", ")}.</Text>
      {youtube && (
        <Text style={{ color: c.muted, fontSize: 12 }}>
          Video önerileri YouTube API Hizmetleri ile bulunur: {join(YOUTUBE_LINKS, " · ")}.
        </Text>
      )}
      <Text style={{ color: c.muted, fontSize: 12 }}>This service uses the ESCO classification of the European Commission.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  head: { flexDirection: "row", alignItems: "center", gap: 16 },
  score: { width: 84, height: 84, borderRadius: 42, borderWidth: 6, alignItems: "center", justifyContent: "center" },
  scoreText: { fontSize: 26, fontWeight: "800" },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  gap: { gap: 6, paddingTop: 8 },
  gapTitle: { fontSize: 16, fontWeight: "700" },
  resource: { borderWidth: 1, borderRadius: 8, padding: 12, gap: 2, minHeight: 44 },
  stars: { flexDirection: "row", gap: 4 },
  star: { minWidth: 44, minHeight: 44, alignItems: "center", justifyContent: "center" },
  attribution: { gap: 6, paddingVertical: 8 },
});
