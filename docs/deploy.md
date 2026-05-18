# 部署说明

## 系统要求

- Docker 20+
- Docker Compose 2+
- 内存: 最低 2GB，推荐 4GB+
- 磁盘: 至少 10GB

## 部署步骤

### 1. 准备服务器

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash

# 安装 Docker Compose
apt-get install docker-compose
```

### 2. 拉取/上传代码

```bash
# 在服务器上创建目录
mkdir -p /opt/prrc
cd /opt/prrc

# 上传 prrc-system 目录到此处
```

### 3. 配置环境变量

```bash
cd /opt/prrc/prrc-system/backend
cp env.sample .env
# 编辑 .env，修改 JWT_SECRET 为随机字符串
vim .env
```

### 4. 启动服务

```bash
cd /opt/prrc/prrc-system

# 第一次启动
docker-compose up -d mysql backend

# 等待 MySQL 就绪（约10秒）
sleep 10

# 导入种子数据
docker exec prrc_backend python -m seeds.import_seed

# 启动前端
docker-compose up -d frontend
```

### 5. 验证

```bash
# 检查健康状态
curl http://localhost:8000/api/v1/health
# 期望返回: {"status":"ok"}

# 访问前端
open http://localhost
```

### 6. 生产环境安全加固

- [ ] 修改 `.env` 中的 `JWT_SECRET`（至少32位随机字符串）
- [ ] 修改 MySQL `MYSQL_ROOT_PASSWORD` 和 `MYSQL_PASSWORD`
- [ ] 开放防火墙端口: `80`, `8000`, `3306`（如需远程访问MySQL）
- [ ] 使用 Nginx HTTPS 反向代理（生产务必 HTTPS）
- [ ] 限制 MySQL 端口仅对内网开放

## 目录权限

```bash
# 数据目录（MySQL 数据持久化）
mkdir -p /opt/prrc-data/mysql
chmod 777 /opt/prrc-data/mysql

# Docker 数据卷自动创建，也可指定路径:
# 在 docker-compose.yml 的 mysql.volumes 中指定
```

## 日志查看

```bash
# 后端日志
docker logs -f prrc_backend

# 前端日志
docker logs -f prrc_frontend

# MySQL 日志
docker exec prrc_mysql cat /var/log/mysql/error.log
```

## 数据备份

```bash
# 备份 MySQL 数据（容器内执行）
docker exec prrc_mysql mysqldump -uroot -proot123 prrc > backup_$(date +%Y%m%d).sql

# 从备份恢复
docker exec -i prrc_mysql mysql -uroot -proot123 prrc < backup_20260518.sql
```

## 更新部署

```bash
cd /opt/prrc/prrc-system
git pull  # 或上传新代码

# 重新构建并启动
docker-compose build backend frontend
docker-compose up -d
```

## 卸载

```bash
cd /opt/prrc/prrc-system
docker-compose down -v  # -v 同时删除数据卷
rm -rf /opt/prrc-data
```
