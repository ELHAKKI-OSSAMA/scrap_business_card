# syntax=docker/dockerfile:1.7
# Builds the business-card web app (APP=business-card-web) and serves it with nginx.
FROM node:22-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
COPY packages/ui/package.json packages/ui/package.json
COPY packages/shared-types/package.json packages/shared-types/package.json
COPY apps/business-card-web/package.json apps/business-card-web/package.json
RUN npm ci --no-audit --no-fund
COPY packages/ui packages/ui
COPY packages/shared-types packages/shared-types
ARG APP
ARG BASE_PATH
COPY apps/${APP} apps/${APP}
ENV VITE_BASE=${BASE_PATH}
RUN npm run build -w apps/${APP}

FROM nginx:1.27-alpine
ARG APP
ARG BASE_PATH
COPY --from=build /src/apps/${APP}/dist /usr/share/nginx/html${BASE_PATH}
COPY infrastructure/nginx/spa.conf.template /etc/nginx/templates/default.conf.template
ENV BASE_PATH=${BASE_PATH}
RUN chown -R nginx:nginx /usr/share/nginx/html
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD wget -qO- "http://127.0.0.1:8081${BASE_PATH}" >/dev/null || exit 1
EXPOSE 8081
