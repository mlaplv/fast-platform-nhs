import os
import httpx
import logging
import random
import string
import uuid
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
from litestar.exceptions import ClientException, NotAuthorizedException

logger = logging.getLogger("api-gateway")

class OAuth2Service:
    @property
    def frontend_url(self) -> str:
        app_domain = os.getenv("APP_DOMAIN", "micsmo.com")
        # Tuân thủ luật SSOT từ .env: APP_URL thay vì hardcode localhost
        return os.getenv("APP_URL", f"https://{app_domain}").rstrip('/')
        
    def _get_redirect_uri(self, provider: str) -> str:
        # Sử dụng API_URL thay vì APP_URL vì Controller Auth nằm ở Backend (api.micsmo.com)
        # Tuân thủ SSOT: Facebook/Google sẽ callback về đúng Endpoint xử lý code.
        api_url = os.getenv("API_URL", "").rstrip('/')
        if not api_url:
            # Fallback nếu API_URL chưa set thì dùng FRONTEND_URL/api...
            base_url = os.getenv("FRONTEND_URL", "https://micsmo.com").rstrip('/')
            return f"{base_url}/api/v1/auth/oauth/callback/{provider}"
        return f"{api_url}/api/v1/auth/oauth/callback/{provider}"

    def get_login_url(self, provider: str) -> str:
        """Sinh ra Access URL để chuyển hướng User sang nền tảng chỉ định."""
        state = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        redirect_uri = self._get_redirect_uri(provider)
        
        if provider == "google":
            client_id = os.getenv("GOOGLE_CLIENT_ID", "")
            if not client_id:
                raise ClientException(status_code=500, detail="Chưa cấu hình GOOGLE_CLIENT_ID")
            
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online"
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
            
        elif provider == "facebook":
            client_id = os.getenv("FACEBOOK_CLIENT_ID", "")
            if not client_id:
                raise ClientException(status_code=500, detail="Chưa cấu hình FACEBOOK_CLIENT_ID")
                
            # Sử dụng v18.0 và comma-separated scope (Fix kịch trần lỗi Invalid Scopes)
            base_url = "https://www.facebook.com/v18.0/dialog/oauth"
            scope = "public_profile,email"
            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "response_type": "code"
            }
            return f"{base_url}?{urlencode(params)}&scope={scope}"
            
        elif provider == "zalo":
            app_id = os.getenv("ZALO_APP_ID", "")
            if not app_id:
                raise ClientException(status_code=500, detail="Chưa cấu hình ZALO_APP_ID")
                
            params = {
                "app_id": app_id,
                "redirect_uri": redirect_uri,
                "state": state
            }
            # Zalo uses a bespoke login portal
            return f"https://oauth.zaloapp.com/v4/permission?{urlencode(params)}"
            
        else:
            raise ClientException(status_code=400, detail=f"Provider {provider} không được hỗ trợ.")

    async def exchange_code_for_user(self, provider: str, code: str) -> Dict[str, str]:
        """Đổi Authorization Code lấy Access Token và trích xuất User Profile (Email, Name, Picture)."""
        redirect_uri = self._get_redirect_uri(provider)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "google":
                return await self._process_google(client, code, redirect_uri)
            elif provider == "facebook":
                return await self._process_facebook(client, code, redirect_uri)
            elif provider == "zalo":
                return await self._process_zalo(client, code, redirect_uri)
            else:
                raise ClientException(status_code=400, detail=f"Provider {provider} không được hỗ trợ.")

    async def _process_google(self, client: httpx.AsyncClient, code: str, redirect_uri: str) -> Dict[str, str]:
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        
        # 1. Exchange Code
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        })
        
        if token_res.status_code != 200:
            logger.error(f"[OAuth Google] Token Exchange Failed: {token_res.text}")
            raise NotAuthorizedException("Google Login Failed.")
            
        acc_token = token_res.json().get("access_token")
        
        # 2. Extract Info (Dùng v3 UserInfo cho độ chính xác dữ liệu cao nhất 2026)
        user_res = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={
            "Authorization": f"Bearer {acc_token}"
        })
        if user_res.status_code != 200:
            logger.error(f"[OAuth Google] API Failed: {user_res.text}")
            raise NotAuthorizedException("Google Info Fetch Failed.")
            
        profile = user_res.json()
        return {
            "email": profile.get("email", ""),
            "name": profile.get("name", "Người dùng Google"),
            "provider_id": profile.get("id", ""),
            "avatar": profile.get("picture", "")
        }

    async def _process_facebook(self, client: httpx.AsyncClient, code: str, redirect_uri: str) -> Dict[str, str]:
        client_id = os.getenv("FACEBOOK_CLIENT_ID", "")
        client_secret = os.getenv("FACEBOOK_CLIENT_SECRET", "")
        
        # 1. Exchange Code
        token_res = await client.get(f"https://graph.facebook.com/v25.0/oauth/access_token", params={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code
        })
        if token_res.status_code != 200:
            logger.error(f"[OAuth Facebook] Token Exchange Failed: {token_res.text}")
            raise NotAuthorizedException("Facebook Login Failed.")
            
        acc_token = token_res.json().get("access_token")
        
        # 2. Extract Info
        user_res = await client.get("https://graph.facebook.com/me", params={
            "fields": "id,name,email,picture.type(large)",
            "access_token": acc_token
        })
        if user_res.status_code != 200:
            logger.error(f"[OAuth Facebook] API Failed: {user_res.text}")
            raise NotAuthorizedException("Facebook Info Fetch Failed.")
            
        profile = user_res.json()
        
        # Parse Avatar
        avatar = ""
        pic_dict = profile.get("picture", {})
        if isinstance(pic_dict, dict) and "data" in pic_dict:
            avatar = pic_dict["data"].get("url", "")
            
        return {
            "email": profile.get("email", ""),
            "name": profile.get("name", "Người dùng Facebook"),
            "provider_id": profile.get("id", ""),
            "avatar": avatar
        }

    async def _process_zalo(self, client: httpx.AsyncClient, code: str, redirect_uri: str) -> Dict[str, str]:
        app_id = os.getenv("ZALO_APP_ID", "")
        secret_key = os.getenv("ZALO_SECRET_KEY", "")
        
        # 1. Exchange Code
        token_res = await client.post("https://oauth.zaloapp.com/v4/access_token", headers={
            "app_id": app_id,
            "secret_key": secret_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }, data={
            "code": code,
            "app_id": app_id,
            "grant_type": "authorization_code"
        })
        
        if token_res.status_code != 200:
            logger.error(f"[OAuth Zalo] Token Exchange Failed: {token_res.text}")
            raise NotAuthorizedException("Zalo Login Failed.")
            
        acc_token = token_res.json().get("access_token")
        
        # 2. Extract Info
        user_res = await client.get("https://graph.zalo.me/v2.0/me", params={
            "fields": "id,name,picture"
        }, headers={
            "access_token": acc_token
        })
        
        if user_res.status_code != 200:
            logger.error(f"[OAuth Zalo] API Failed: {user_res.text}")
            raise NotAuthorizedException("Zalo Info Fetch Failed.")
            
        profile = user_res.json()
        avatar = ""
        pic_dict = profile.get("picture", {})
        if isinstance(pic_dict, dict) and "data" in pic_dict:
            avatar = pic_dict["data"].get("url", "")
            
        return {
            "email": "",  # Zalo often does not return email by default unless permitted
            "name": profile.get("name", "Người dùng Zalo"),
            "provider_id": profile.get("id", ""),
            "avatar": avatar
        }

oauth2_service = OAuth2Service()
