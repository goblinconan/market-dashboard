FROM node:20-alpine AS build

WORKDIR /app

# 使用国内 npm 镜像，避免拉包超时
RUN npm config set registry https://registry.npmmirror.com/

# 路径相对于 docker-compose 中的 context: .
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# nginx 配置也相对于根目录
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]