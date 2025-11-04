#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${POSTGRES_DB:-postgres}"
echo "▶ Initialisierung für Datenbank: ${DB_NAME}"

run_sql() {
  local file="$1"
  echo "   - wende Schema an: ${file}"
  psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${DB_NAME}" -f "/docker-entrypoint-initdb.d/sql/${file}"
}

case "${DB_NAME}" in
  auth_db)
    run_sql "auth_db.sql"
    ;;
  customer_db)
    run_sql "customer_db.sql"
    ;;
  portal_users_db)
    run_sql "portal_users_db.sql"
    ;;
  business_db1|business_db2|business_db3)
    run_sql "business_db.sql"
    ;;
  admin_db)
    run_sql "admin_db.sql"
	;;
  *)
    echo "⚠ Keine passende Init-Datei für DB '${DB_NAME}'. Überspringe."
    ;;
esac

echo "✔ Init abgeschlossen für ${DB_NAME}"
