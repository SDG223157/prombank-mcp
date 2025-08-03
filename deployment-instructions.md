# Coolify Deployment Instructions for Prombank MCP

## Prerequisites

1. Coolify instance running
2. MySQL database configured (provided connection string)
3. Docker support enabled

## Deployment Steps

### 1. Environment Variables in Coolify

Set these environment variables in your Coolify project:

```bash
# Database
DATABASE_URL=mysql+pymysql://mysql:mQ4z935UA5wSTJFubrdLCDLyFRYS50I7yvPjRKvt7UkcfwtiAh8Zk9RuJuOcE66v@toowk4ok4ok0w4sgkgc8wsw0:3306/default

# Application
SECRET_KEY=your-super-secret-key-change-me-in-production-$(openssl rand -hex 32)
APP_PORT=8000

# Optional: Logging
LOG_LEVEL=info
ENVIRONMENT=production
```

### 2. Repository Setup

1. Push your code to a Git repository (GitHub, GitLab, etc.)
2. Make sure all files are committed including:
   - `Dockerfile`
   - `coolify-docker-compose.yml`
   - `entrypoint.sh`
   - Updated `requirements.txt` with MySQL dependencies

### 3. Coolify Configuration

1. **Create New Project** in Coolify
2. **Source**: Connect your Git repository
3. **Build Type**: Choose "Docker Compose"
4. **Compose File**: Use `coolify-docker-compose.yml`
5. **Port Mapping**: Map port 8000
6. **Environment Variables**: Add the variables from step 1

### 4. Domain Configuration

1. Set up your domain in Coolify
2. Configure SSL/TLS certificate (Let's Encrypt recommended)
3. Set up any necessary proxy rules

### 5. Health Checks

The application includes built-in health checks:
- Endpoint: `GET /health`
- Docker health check configured
- Database connection verification

## Post-Deployment Verification

### 1. Check Application Health
```bash
curl https://your-domain.com/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

### 2. Access API Documentation
Visit: `https://your-domain.com/docs`

### 3. Test Basic Functionality
```bash
# List prompts
curl https://your-domain.com/api/v1/prompts

# Create a test prompt
curl -X POST https://your-domain.com/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Prompt", "content": "Hello from production!"}'
```

## MCP Server Setup (Optional)

If you want to run the MCP server in production:

1. **Add MCP Service** to `coolify-docker-compose.yml`:
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
3. **Configure Client** to connect to `your-domain.com:8001`

## Monitoring and Logs

### View Logs
In Coolify dashboard:
1. Go to your project
2. Click on "Logs" tab
3. Monitor application startup and runtime logs

### Key Log Messages to Look For
- "Database connection successful!"
- "Database initialization complete!"
- "Starting application..."
- Health check responses

## Troubleshooting

### Database Connection Issues
1. Verify MySQL credentials
2. Check network connectivity
3. Ensure database exists and is accessible

### Build Issues
1. Check Dockerfile syntax
2. Verify all dependencies in requirements.txt
3. Ensure Python version compatibility

### Runtime Issues
1. Check environment variables
2. Verify port mappings
3. Review application logs

## Scaling and Performance

### Resource Limits
Current configuration:
- Memory: 512MB limit, 256MB reserved
- Workers: 4 Gunicorn workers
- Timeout: 120 seconds

### Scaling Options
1. **Horizontal**: Deploy multiple instances behind load balancer
2. **Vertical**: Increase memory/CPU limits in docker-compose
3. **Database**: Consider connection pooling for high load

## Backup and Maintenance

### Database Backups
Set up regular MySQL backups through your hosting provider or Coolify backup features.

### Application Data
The `/app/data` and `/app/backups` volumes are persistent and should be included in backup strategies.

### Updates
1. Push code changes to repository
2. Coolify will automatically redeploy
3. Database migrations run automatically on startup

## Security Considerations

1. **Change SECRET_KEY**: Use a strong, random secret key
2. **Database Security**: Ensure MySQL has proper access controls
3. **HTTPS**: Always use SSL/TLS in production
4. **Environment Variables**: Never commit sensitive data to repository
5. **Regular Updates**: Keep dependencies updated

## Support

For issues:
1. Check Coolify logs
2. Review application logs
3. Verify database connectivity
4. Check environment variable configuration