; Windows kaldırıcısına eklenen adım (electron-builder, buildResources/installer.nsh otomatik okunur).
; Uygulama kaldırılınca %APPDATA%\CareerAI silinir: oturum (7 günlük refresh token localStorage'da), önbellek ve
; güncelleme kaydı bilgisayarda kalmasın. Ortak bilgisayarda yeniden kurulan uygulama önceki kullanıcıyla açılmasın
; (docs/kurulum/masaustu-kurulum.md "Kaldırma"). Klasör adı main.cjs'teki userData yoluyla aynıdır (eski adla sabit).
; Otomatik güncelleme eski sürümü de bu kaldırıcıyla siler; o durumda (isUpdated) oturum korunur.
!macro customUnInstall
  ${ifNot} ${isUpdated}
    RMDir /r "$APPDATA\CareerAI"
  ${endIf}
!macroend
