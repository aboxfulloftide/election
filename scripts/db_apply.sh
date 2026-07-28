#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env with database connection details." >&2
  exit 1
fi

DB_HOST=""
DB_PORT="3306"
DB_USER=""
DB_PASSWORD=""
DB_NAME=""

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

while IFS= read -r line || [[ -n "$line" ]]; do
  line="$(trim "$line")"
  [[ -z "$line" || "${line:0:1}" == "#" ]] && continue

  if [[ "$line" == *=* ]]; then
    key="$(trim "${line%%=*}")"
    value="$(trim "${line#*=}")"
  elif [[ "$line" == *:* ]]; then
    key="$(trim "${line%%:*}")"
    value="$(trim "${line#*:}")"
  else
    continue
  fi

  case "$key" in
    DB_HOST|MYSQL_HOST|host) DB_HOST="$value" ;;
    DB_PORT|MYSQL_PORT|port) DB_PORT="$value" ;;
    DB_USER|MYSQL_USER|user) DB_USER="$value" ;;
    DB_PASSWORD|MYSQL_PASSWORD|pass|password) DB_PASSWORD="$value" ;;
    DB_NAME|MYSQL_DATABASE|database|db) DB_NAME="$value" ;;
  esac
done < "$ENV_FILE"

if [[ -z "$DB_HOST" || -z "$DB_USER" || -z "$DB_NAME" ]]; then
  echo "Missing DB host, user, or database name in .env." >&2
  exit 1
fi

DEFAULTS_FILE="$(mktemp)"
trap 'rm -f "$DEFAULTS_FILE"' EXIT
chmod 600 "$DEFAULTS_FILE"

cat > "$DEFAULTS_FILE" <<EOF
[client]
host=$DB_HOST
port=$DB_PORT
user=$DB_USER
password=$DB_PASSWORD
default-character-set=utf8mb4
EOF

mysql_base=(mysql --defaults-extra-file="$DEFAULTS_FILE" --batch --raw)

echo "Ensuring database exists..."
"${mysql_base[@]}" --execute="CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"

echo "Applying migrations..."
for file in "$ROOT_DIR"/db/migrations/*.sql; do
  [[ -e "$file" ]] || continue
  echo "  $(basename "$file")"
  "${mysql_base[@]}" "$DB_NAME" < "$file"
done

echo "Applying seeds..."
for file in "$ROOT_DIR"/db/seeds/*.sql; do
  [[ -e "$file" ]] || continue
  echo "  $(basename "$file")"
  "${mysql_base[@]}" "$DB_NAME" < "$file"
done

echo "Database is ready."
