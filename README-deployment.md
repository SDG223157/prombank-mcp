# 🚀 Coolify Deployment Guide for Prombank MCP

## Quick Deployment Summary

Your Prombank MCP system is now ready for deployment on Coolify with MySQL support!

### 📋 What's Been Configured

✅ **MySQL Database Support** - Updated for your provided MySQL connection  
✅ **Docker Configuration** - Multi-stage Dockerfile with health checks  
✅ **Production Environment** - Environment variables and settings  
✅ **Database Migrations** - Alembic configured for MySQL  
✅ **Coolify Integration** - Docker Compose configuration for Coolify  
✅ **Auto-initialization** - Database setup and migration on startup  

## 🔧 Environment Variables for Coolify

Set these in your Coolify project environment:

```bash
# Database (your provided connection)
DATABASE_URL=mysql+pymysql://mysql:mQ4z935UA5wSTJFubrdLCDLyFRYS50I7yvPjRKvt7UkcfwtiAh8Zk9RuJuOcE66v@toowk4ok4ok0w4sgkgc8wsw0:3306/default

# Security (CHANGE THIS!)
SECRET_KEY=your-super-secret-key-$(openssl rand -hex 32)

# Application
APP_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=info
```

## 📂 Files for Deployment

Your project now includes:

- `Dockerfile` - Production-ready container
- `coolify-docker-compose.yml` - Coolify deployment configuration
- `entrypoint.sh` - Startup script with database initialization
- `requirements.txt` - Updated with MySQL dependencies
- Database migrations in `alembic/versions/`

## 🚀 Deployment Steps

### 1. Push to Git Repository
```bash
git add .
git commit -m "Prepare for Coolify deployment with MySQL"
git push origin main
```

### 2. Create Coolify Project
1. New Project → Docker Compose
2. Connect your Git repository
3. Set compose file: `coolify-docker-compose.yml`
4. Add environment variables above

### 3. Deploy!
Coolify will automatically:
- Build the Docker image
- Wait for database connection
- Run migrations
- Initialize default data
- Start the application

## 🔍 Verification

After deployment, test these endpoints:

```bash
# Health check
curl https://your-domain.com/health

# API documentation
https://your-domain.com/docs

# List prompts
curl https://your-domain.com/api/v1/prompts

# Create test prompt
curl -X POST https://your-domain.com/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{"title": "Production Test", "content": "Hello from Coolify!"}'
```

## 🛠 Features Available

### REST API
- Full CRUD operations for prompts
- Search and filtering
- Category and tag management
- Import/export functionality
- OpenAPI documentation at `/docs`

### MCP Server (Optional)
Add this service to docker-compose for MCP integration:

```yaml
  prombank-mcp:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PROMBANK_DATABASE_URL=${DATABASE_URL}
    command: ["python", "-m", "prombank.mcp_server"]
```

## 📊 Monitoring

### Health Check
- Endpoint: `GET /health`
- Docker health checks included
- Database connection verification

### Logs
Monitor through Coolify dashboard:
- Application startup logs
- Database migration logs
- Runtime application logs

## 🔧 Configuration Options

### Resource Limits
Default configuration:
- Memory: 512MB limit
- Workers: 4 Gunicorn workers
- Timeout: 120 seconds

### Scaling
Adjust in `coolify-docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

## 🔒 Security Checklist

- ✅ Change SECRET_KEY to random value
- ✅ Use HTTPS/SSL in production
- ✅ Database credentials secured
- ✅ No sensitive data in git repository
- ✅ Environment variables properly configured

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify MySQL connection string
   - Check network access to database
   - Ensure database exists

2. **Build Failures**
   - Check Dockerfile syntax
   - Verify all files are committed
   - Review build logs in Coolify

3. **Migration Errors**
   - Database permissions
   - Table conflicts
   - Check migration logs

### Support Commands

```bash
# Test database connection locally
python -c "from src.prombank.database import SessionLocal; db = SessionLocal(); print('DB Connected!')"

# Run migrations manually
alembic upgrade head

# Check application health
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

## 🎉 Success!

Your Prombank MCP system should now be running on Coolify with:
- MySQL database integration
- Production-ready configuration
- Automatic health monitoring
- Complete prompt management features

Access your deployed application and start managing prompts with full MCP integration capabilities!