# Build Stage
FROM node:22-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production Stage (Nginx)
FROM nginx:alpine AS production-stage
# 위에서 생성한 nginx.conf 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 빌드된 결과물을 Nginx 서빙 디렉토리로 복사
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
