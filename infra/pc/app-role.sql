-- En az yetkili uygulama rolü (T-075). API ve veri işçisi production'da bununla bağlanır (compose.yml, x-app-env).
-- Migration, yedek ve elle bakım POSTGRES_USER (sahip) ile yapılır; bu rol tablo oluşturamaz, silemez, şema değiştiremez.
-- deploy.sh her deploy'da migration'dan SONRA çalıştırır: yeni tablolar da yetki alır. Şifre psql değişkeniyle gelir
-- (`\set app_pw …` girişin başında, komut satırında görünmez). Test: backend/tests/db/test_app_role.py.
SET client_min_messages = warning;

DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'careerai_app') THEN CREATE ROLE careerai_app LOGIN; END IF;
END $$;
ALTER ROLE careerai_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
  CONNECTION LIMIT 40 PASSWORD :'app_pw';

DO $$ BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO careerai_app', current_database());
END $$;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO careerai_app;

-- Veri: okuma ve yazma, yapı değil (TRUNCATE, REFERENCES, TRIGGER yok).
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO careerai_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO careerai_app;
-- role_skill_stats yenileme (migration 0004); view'ın sahibi olmadan.
GRANT EXECUTE ON FUNCTION refresh_role_skill_stats(boolean) TO careerai_app;

-- Denetim kaydı sadece eklenir ve okunur: uygulama geçmişi değiştiremez (KVKK hesap silme kaydı dahil).
-- Kullanıcı silinince user_id'nin NULL olması FK işlemidir, tablo sahibinin yetkisiyle çalışır.
REVOKE UPDATE, DELETE ON audit_logs FROM careerai_app;
-- Migration sürümü uygulamanın işi değil.
REVOKE ALL ON alembic_version FROM careerai_app;
