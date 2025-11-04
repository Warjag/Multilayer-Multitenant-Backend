FROM postgres:15

# Kopiere alle Init-Skripte ins Standard-Init-Verzeichnis
COPY initdb/ /docker-entrypoint-initdb.d/

# Sicherstellen: Shell-Script ist ausführbar und hat Linux-Zeilenenden (LF)
RUN set -eux; \
    chmod +x /docker-entrypoint-initdb.d/01-init-router.sh; \
    sed -i 's/\r$//' /docker-entrypoint-initdb.d/01-init-router.sh
