# 🚀 Deploy Prombank MCP to Coolify - Step by Step

## Pre-Deployment Checklist

✅ **MySQL Database** - Your connection string ready  
✅ **Git Repository** - Code pushed to GitHub/GitLab  
✅ **Coolify Instance** - Running and accessible  
✅ **Docker Support** - Enabled in Coolify  

## Step 1: Environment Variables

In your Coolify project, set these environment variables:

```bash
# 🔥 CRITICAL: Database Connection
DATABASE_URL=mysql+pymysql://mysql:mQ4z935UA5wSTJFubrdLCDLyFRYS50I7yvPjRKvt7UkcfwtiAh8Zk9RuJuOcE66v@toowk4ok4ok0w4sgkgc8wsw0:3306/default

# 🔐 Security (CHANGE THIS!)
SECRET_KEY=your-super-secret-production-key-$(openssl rand -hex 32)

# 🌐 Application Settings
APP_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=info
```

## Step 2: Coolify Project Setup

1. **Create New Project** in Coolify
2. **Source Type**: Git Repository
3. **Repository**: Connect your GitHub/GitLab repo
4. **Branch**: `main` (or your deployment branch)
5. **Build Pack**: Docker Compose
6. **Compose File**: `coolify-docker-compose.yml`

## Step 3: Configuration

### Port Mapping
- **Container Port**: 8000
- **Public Port**: 80/443 (for HTTP/HTTPS)

### Health Check
- **Endpoint**: `/health`
- **Timeout**: 30 seconds
- **Retries**: 3

### Volumes (Optional)
- `/app/data` - For persistent application data
- `/app/backups` - For backup storage

## Step 4: Domain & SSL

1. **Add Domain** in Coolify
2. **Enable SSL/TLS** (Let's Encrypt recommended)
3. **Force HTTPS** for security

## Step 5: Deploy! 🚀

Click **Deploy** in Coolify. The system will:

1. 📥 **Pull Code** from your repository
2. 🏗️ **Build Docker Image** with all dependencies
3. 🔄 **Wait for Database** connection (up to 30 retries)
4. 📊 **Run Migrations** to create tables
5. 🌱 **Initialize Default Data** (categories, etc.)
6. 🚀 **Start Application** on port 8000

## Step 6: Verification

### Quick Health Check
```bash
curl https://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected", 
  "version": "0.1.0"
}
```

### API Documentation
Visit: `https://your-domain.com/docs`

### Test Basic Operations
```bash
# List prompts (should be empty initially)
curl https://your-domain.com/api/v1/prompts

# Create first prompt
curl -X POST https://your-domain.com/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Welcome to Production!",
    "content": "This is your first prompt in production!",
    "description": "Created via API on Coolify deployment"
  }'
```

## Monitoring & Troubleshooting

### 📊 Check Logs
In Coolify Dashboard:
1. Go to your project
2. Click **Logs** tab
3. Look for these success messages:
   - "Database connection successful!"
   - "Database initialization complete!"
   - "Starting application..."

### 🔧 Common Issues

**Database Connection Failed**
- Verify MySQL credentials in environment variables
- Check database server accessibility
- Ensure database exists and has proper permissions

**Build Failures**
- Check Dockerfile syntax in logs
- Verify all dependencies in requirements.txt
- Ensure Python version compatibility

**Migration Errors**
- Database permissions issues
- Check if tables already exist
- Review migration logs in container

### 🚨 Emergency Commands

If you need to debug, you can exec into the container:

```bash
# In Coolify terminal or SSH
docker exec -it <container-name> bash

# Check database connection
python -c "from src.prombank.database import SessionLocal; db = SessionLocal(); print('DB OK!')"

# Run migrations manually
alembic upgrade head

# Check app health
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

## Optional: MCP Server Deployment

To also run the MCP server for Cursor integration:

1. **Update** `coolify-docker-compose.yml` to add:
```yaml
  prombank-mcp:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PROMBANK_DATABASE_URL=${DATABASE_URL}
      - PROMBANK_MCP_HOST=0.0.0.0
      - PROMBANK_MCP_PORT=8001
    command: ["python", "-m", "prombank.mcp_server"]
    restart: unless-stopped
```

2. **Expose Port 8001** in Coolify
3. **Connect Cursor** to `your-domain.com:8001`

## Production Checklist

Before going live:

- [ ] Change SECRET_KEY to random value
- [ ] Enable HTTPS/SSL
- [ ] Set up regular database backups
- [ ] Configure monitoring/alerting
- [ ] Test all API endpoints
- [ ] Verify MCP tools work (if deployed)
- [ ] Document access credentials securely

## Success! 🎉

Your Prombank MCP system is now running in production on Coolify with:

✅ **Full CRUD Operations** - Create, read, update, delete prompts  
✅ **Search & Filter** - Find prompts by content, tags, categories  
✅ **Import/Export** - Multiple format support  
✅ **Version History** - Track prompt changes  
✅ **REST API** - Complete HTTP API with docs  
✅ **MySQL Integration** - Production database  
✅ **Health Monitoring** - Built-in health checks  
✅ **Auto-scaling Ready** - Docker containerized  

Access your new prompt management system and start organizing your AI prompts professionally!