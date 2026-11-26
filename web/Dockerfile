# =====================================================================
# Imagem 3 de 3: front-end do PontoZero (React + Vite servido pelo Nginx)
#
# Etapa 1 compila o React com Node. Etapa 2 copia só os arquivos prontos
# para uma imagem pequena do Nginx: o Node não vai para a imagem final.
# =====================================================================
FROM node:22-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
LABEL org.opencontainers.image.title="pontozero-web" \
      org.opencontainers.image.description="Front-end do PontoZero (React) servido pelo Nginx" \
      org.opencontainers.image.vendor="Equipe PontoZero"

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/saude >/dev/null || exit 1
