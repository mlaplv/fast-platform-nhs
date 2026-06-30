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
        app_domain = os.getenv("APP_DOMAIN", "osmo")
        # Tuân thủ luật SSOT từ .env: APP_URL thay vì hardcode localhost
        return os.getenv("APP_URL", f"https://{app_domain}").rstrip('/')
        
    def _get_redirect_uri(self, provider: str) -> str:
        provider_clean = provider.rstrip('/')
        # Zalo yêu cầu xác thực tên miền chính, bắt buộc dùng APP_URL (osmo.vn) làm Callback
        if provider_clean == "zalo":
            base_url = os.getenv("APP_URL", "https://osmo.vn").rstrip('/')
            return f"{base_url}/api/v1/auth/oauth/callback/zalo"

        # TikTok Sandbox yêu cầu dấu gạch chéo ngược ở cuối để khớp chính xác cấu hình Developer Console
        suffix = "/" if provider_clean == "tiktok" else ""

        # Sử dụng API_URL thay vì APP_URL vì Controller Auth nằm ở Backend (api.osmo)
        # Tuân thủ SSOT: Facebook/Google/Zalo sẽ callback về đúng Endpoint xử lý code.
        api_url = os.getenv("API_URL", "").rstrip('/')
        if not api_url:
            # Fallback nếu API_URL chưa set thì dùng FRONTEND_URL/api...
            base_url = os.getenv("FRONTEND_URL", "https://osmo").rstrip('/')
            return f"{base_url}/api/v1/auth/oauth/callback/{provider_clean}{suffix}"
        return f"{api_url}/api/v1/auth/oauth/callback/{provider_clean}{suffix}"

    def get_login_url(self, provider: str, custom_state: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """Sinh ra Access URL để chuyển hướng User sang nền tảng chỉ định."""
        provider = provider.rstrip('/')
        state = custom_state or "".join(random.choices(string.ascii_letters + string.digits, k=32))
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
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}", None
            
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
            return f"{base_url}?{urlencode(params)}&scope={scope}", None
            
        elif provider == "zalo":
            app_id = os.getenv("ZALO_APP_ID") or os.getenv("ZALO_CLIENT_ID", "")
            if not app_id:
                raise ClientException(status_code=500, detail="Chưa cấu hình ZALO_APP_ID")
                
            import secrets
            import hashlib
            import base64

            # PKCE: Generate code_verifier (random string, 43 to 128 characters)
            code_verifier = secrets.token_urlsafe(64)[:64]
            # PKCE: Generate code_challenge
            hashed = hashlib.sha256(code_verifier.encode('ascii')).digest()
            code_challenge = base64.urlsafe_b64encode(hashed).decode('ascii').replace('=', '')

            params = {
                "app_id": app_id,
                "redirect_uri": redirect_uri,
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            }
            # Zalo uses a bespoke login portal requiring PKCE
            return f"https://oauth.zaloapp.com/v4/permission?{urlencode(params)}", code_verifier
            
        elif provider == "tiktok":
            client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
            if not client_key:
                raise ClientException(status_code=500, detail="Chưa cấu hình TIKTOK_CLIENT_KEY")
            
            base_url = "https://www.tiktok.com/v2/auth/authorize/"
            params = {
                "client_key": client_key,
                "scope": "user.info.basic",
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "state": state
            }
            return f"{base_url}?{urlencode(params)}", None
            
        else:
            raise ClientException(status_code=400, detail=f"Provider {provider} không được hỗ trợ.")

    async def exchange_code_for_user(self, provider: str, code: str, code_verifier: Optional[str] = None) -> Dict[str, str]:
        """Đổi Authorization Code lấy Access Token và trích xuất User Profile (Email, Name, Picture)."""
        provider = provider.rstrip('/')
        redirect_uri = self._get_redirect_uri(provider)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "google":
                return await self._process_google(client, code, redirect_uri)
            elif provider == "facebook":
                return await self._process_facebook(client, code, redirect_uri)
            elif provider == "zalo":
                return await self._process_zalo(client, code, redirect_uri, code_verifier)
            elif provider == "tiktok":
                return await self._process_tiktok(client, code, redirect_uri)
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
            "avatar": avatar,
            "access_token": acc_token
        }

    async def _process_zalo(self, client: httpx.AsyncClient, code: str, redirect_uri: str, code_verifier: Optional[str] = None) -> Dict[str, str]:
        app_id = os.getenv("ZALO_APP_ID") or os.getenv("ZALO_CLIENT_ID", "")
        secret_key = os.getenv("ZALO_SECRET_KEY") or os.getenv("ZALO_CLIENT_SECRET", "")
        
        if not app_id or not secret_key:
            raise ClientException(status_code=500, detail="Chưa cấu hình thông tin xác thực Zalo")
        
        # 1. Exchange Code
        data = {
            "code": code,
            "app_id": app_id,
            "grant_type": "authorization_code"
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        token_res = await client.post("https://oauth.zaloapp.com/v4/access_token", headers={
            "app_id": app_id,
            "secret_key": secret_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=data)
        
        if token_res.status_code != 200:
            logger.error(f"[OAuth Zalo] Token Exchange Failed: {token_res.text}")
            raise NotAuthorizedException("Zalo Login Failed.")
            
        res_json = token_res.json()
        if "error" in res_json or "error_description" in res_json:
            error_msg = res_json.get("error_description") or res_json.get("message") or f"Mã lỗi: {res_json.get('error')}"
            logger.error(f"[OAuth Zalo] API Error inside response: {res_json}")
            raise NotAuthorizedException(f"Zalo Login Failed: {error_msg}")

        acc_token = res_json.get("access_token")
        if not acc_token:
            logger.error(f"[OAuth Zalo] No access_token returned: {res_json}")
            raise NotAuthorizedException("Zalo Login Failed: Không tìm thấy access token.")
        
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

    async def _process_tiktok(self, client: httpx.AsyncClient, code: str, redirect_uri: str) -> Dict[str, str]:
        client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
        
        if not client_key or not client_secret:
            raise ClientException(status_code=500, detail="Chưa cấu hình thông tin xác thực TikTok")
            
        token_res = await client.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )
        
        if token_res.status_code != 200:
            logger.error(f"[OAuth TikTok] Token Exchange Failed: {token_res.text}")
            raise NotAuthorizedException("TikTok Login Failed.")
            
        res_json = token_res.json()
        if "error" in res_json:
            error_msg = res_json.get("error_description") or f"Mã lỗi: {res_json.get('error')}"
            logger.error(f"[OAuth TikTok] API Error inside response: {res_json}")
            raise NotAuthorizedException(f"TikTok Login Failed: {error_msg}")
            
        access_token = res_json.get("access_token")
        open_id = res_json.get("open_id")
        
        if not access_token:
            logger.error(f"[OAuth TikTok] No access_token returned: {res_json}")
            raise NotAuthorizedException("TikTok Login Failed: Không tìm thấy access token.")
            
        user_res = await client.get(
            "https://open.tiktokapis.com/v2/user/info/",
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_res.status_code != 200:
            logger.error(f"[OAuth TikTok] Fetch User Info Failed: {user_res.text}")
            raise NotAuthorizedException("TikTok Info Fetch Failed.")
            
        profile_json = user_res.json()
        if profile_json.get("error", {}).get("code") != "ok":
            err_msg = profile_json.get("error", {}).get("message", "Unknown error")
            logger.error(f"[OAuth TikTok] Fetch User Info Business Error: {profile_json}")
            raise NotAuthorizedException(f"TikTok Profile Error: {err_msg}")
            
        user_data = profile_json.get("data", {}).get("user", {})
        
        return {
            "email": "",
            "name": user_data.get("display_name") or "Người dùng TikTok",
            "provider_id": user_data.get("open_id") or open_id or "",
            "avatar": user_data.get("avatar_url") or ""
        }

oauth2_service = OAuth2Service()
