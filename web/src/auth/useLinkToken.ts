import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * E-posta bağlantısındaki tek kullanımlık `?token=` değerini bir kez okur ve adres çubuğundan siler:
 * token tarayıcı geçmişinde ve ekran görüntülerinde kalmasın.
 */
export function useLinkToken(): string {
  const [params, setParams] = useSearchParams();
  const [token] = useState(() => params.get("token") ?? "");
  useEffect(() => {
    if (params.has("token")) setParams({}, { replace: true });
  }, [params, setParams]);
  return token;
}
