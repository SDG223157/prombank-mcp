# 🔐 Google OAuth Setup for Prombank MCP

## Step 1: Google Cloud Console Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create New Project** or select existing project
3. **Project Name**: `Prombank MCP` (or your preferred name)

### 1.2 Enable Google+ API

1. Go to **APIs & Services** → **Library**
2. Search for **Google+ API**
3. **Enable** the Google+ API

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. **User Type**: External (for public app)
3. **App Information**:
   - **App name**: `Prombank MCP`
   - **User support email**: Your email
   - **App domain**: `prombank.app`
   - **Developer contact**: Your email
4. **Scopes**: Add these scopes:
   - `openid`
   - `email` 
   - `profile`
5. **Test Users**: Add your email for testing

### 1.4 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth 2.0 Client IDs**
3. **Application Type**: Web application
4. **Name**: `Prombank MCP Web Client`
5. **Authorized JavaScript origins**:
   ```
   https://prombank.app
   http://localhost:3000  (for development)
   ```
6. **Authorized redirect URIs**:
   ```
   https://prombank.app/api/auth/google/callback
   http://localhost:8000/api/auth/google/callback  (for development)
   ```

## Step 2: Environment Variables

Add these to your Coolify environment variables:

```bash
# Google OAuth Configuration
PROMBANK_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
PROMBANK_GOOGLE_CLIENT_SECRET=your-google-client-secret
PROMBANK_GOOGLE_REDIRECT_URI=https://prombank.app/api/auth/google/callback

# Frontend URL
PROMBANK_FRONTEND_URL=https://prombank.app

# JWT Secret (IMPORTANT: Change this!)
PROMBANK_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# JWT Configuration  
PROMBANK_JWT_ALGORITHM=HS256
PROMBANK_ACCESS_TOKEN_EXPIRE_MINUTES=30
PROMBANK_REFRESH_TOKEN_EXPIRE_DAYS=30
```

## Step 3: Update Coolify Deployment

Your existing environment variables for Coolify should now include:

```bash
# Previous variables
DATABASE_URL=mysql+pymysql://mysql:mQ4z935UA5wSTJFubrdLCDLyFRYS50I7yvPjRKvt7UkcfwtiAh8Zk9RuJuOcE66v@toowk4ok4ok0w4sgkgc8wsw0:3306/default
SECRET_KEY=0cb34db80311489038fc7b3684a548c68a772a996a04c39c702980b20726e6d0
APP_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=info

# New OAuth variables
PROMBANK_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
PROMBANK_GOOGLE_CLIENT_SECRET=your-google-client-secret
PROMBANK_GOOGLE_REDIRECT_URI=https://prombank.app/api/auth/google/callback
PROMBANK_FRONTEND_URL=https://prombank.app
```

## Step 4: OAuth Flow Implementation

### 4.1 Available Endpoints

After deployment, your OAuth endpoints will be:

```bash
# Get Google OAuth URL
GET https://prombank.app/api/auth/google
# Returns: {"authorization_url": "https://accounts.google.com/o/oauth2/auth?..."}

# Handle OAuth callback
GET https://prombank.app/api/auth/google/callback?code=xxx&state=xxx
# Returns: JWT tokens and user info

# Login with code (for API clients)
POST https://prombank.app/api/auth/token
Content-Type: application/json
{
  "code": "google-oauth-code",
  "state": "optional-state"
}

# Get current user
GET https://prombank.app/api/auth/me
Authorization: Bearer your-jwt-token

# Refresh token
POST https://prombank.app/api/auth/refresh
Content-Type: application/json
{
  "refresh_token": "your-refresh-token"
}

# Logout
POST https://prombank.app/api/auth/logout
Authorization: Bearer your-jwt-token
```

### 4.2 Frontend Integration Example

```javascript
// 1. Get Google OAuth URL
const response = await fetch('https://prombank.app/api/auth/google');
const { authorization_url } = await response.json();

// 2. Redirect user to Google
window.location.href = authorization_url;

// 3. Handle callback (on your frontend)
// Google will redirect to: https://prombank.app/api/auth/google/callback?code=xxx
// Your API will return JWT tokens

// 4. Use JWT token for authenticated requests
const authResponse = await fetch('https://prombank.app/api/v1/prompts', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

## Step 5: Testing OAuth Flow

### 5.1 Test with cURL

```bash
# 1. Get OAuth URL
curl https://prombank.app/api/auth/google

# 2. Visit the returned URL in browser, complete OAuth
# 3. Google redirects to callback with code

# 4. Test token endpoint (replace with actual code)
curl -X POST https://prombank.app/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"code": "your-oauth-code-from-callback"}'

# 5. Test authenticated endpoint
curl https://prombank.app/api/auth/me \
  -H "Authorization: Bearer your-jwt-token"
```

### 5.2 Expected User Flow

1. **User clicks "Login with Google"**
2. **Frontend calls** `/api/auth/google` to get OAuth URL
3. **User redirected** to Google OAuth consent screen
4. **User grants permissions** and is redirected back
5. **Backend receives code** at `/api/auth/google/callback`
6. **Backend exchanges code** for user info with Google
7. **Backend creates/updates user** in database
8. **Backend returns JWT tokens** to frontend
9. **Frontend stores tokens** and user is logged in

## Step 6: Database Migration

The authentication system requires new database tables. They will be created automatically when you deploy with the new migration:

```bash
# Tables that will be created:
# - users (stores user accounts)
# - user_sessions (tracks active sessions)
```

## Step 7: Security Considerations

### 7.1 Production Checklist

- ✅ **Unique JWT Secret**: Use a strong, random secret key
- ✅ **HTTPS Only**: Ensure all OAuth redirects use HTTPS  
- ✅ **Validate Domains**: Only allow trusted redirect URIs
- ✅ **Token Expiry**: Set appropriate token lifetimes
- ✅ **Session Management**: Implement proper logout and session cleanup

### 7.2 Google OAuth Best Practices

- ✅ **Minimal Scopes**: Only request `openid`, `email`, `profile`
- ✅ **State Parameter**: Use state for CSRF protection
- ✅ **Secure Storage**: Store client secret securely in environment variables
- ✅ **Domain Verification**: Verify your domain in Google Console

## Step 8: Frontend Integration

Your frontend application will need to:

1. **Implement OAuth Flow**: Handle login/logout flows
2. **Store JWT Tokens**: Securely store access/refresh tokens
3. **Token Refresh**: Automatically refresh expired tokens
4. **Authenticated Requests**: Include JWT in API requests

Example frontend code:

```javascript
class AuthService {
  async login() {
    const { authorization_url } = await this.getOAuthUrl();
    window.location.href = authorization_url;
  }
  
  async getOAuthUrl() {
    const response = await fetch('/api/auth/google');
    return response.json();
  }
  
  async getCurrentUser() {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
}
```

## 🎉 Success!

Once configured, your Prombank MCP will have:

✅ **Google OAuth Login** - Users can sign in with Google  
✅ **JWT Authentication** - Secure token-based auth  
✅ **User Management** - User profiles and sessions  
✅ **Protected Endpoints** - Secure API access  
✅ **Session Management** - Login/logout functionality  

Your authentication system is now ready for production! 🚀