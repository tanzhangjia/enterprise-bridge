"""
⚠️ 仅供学习参考 — 两步 RSA 注册认证模式

某些企业系统的认证流程：
1. 发送 APP_ID + 公钥，获取临时凭证 + 服务端公钥
2. 用服务端公钥加密临时凭证换取 token
3. 后续请求带 token + app_id + 加密的 user_id

**此为通用的认证模式抽象，不指向任何具体系统。**
"""
import os, json, base64, subprocess, tempfile
from typing import Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import AuthProvider


class RsaTwoStepAuthProvider(AuthProvider):
    """
    两步 RSA 认证模式。
    
    仅供学习参考，实际对接请遵循目标系统的认证协议。
    """
    name = "rsa_two_step"
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        super().__init__(config)
        self.base_url = self._env("BASE_URL", "")
        self.app_id = self._env("APP_ID", "")
        self.priv_key = self._env("RSA_PRIVATE_KEY", "")
        self.pub_key = self._env("RSA_PUBLIC_KEY", "")
        self._token = None
        self._spk = None
    
    def _env(self, key: str, default: str = "") -> str:
        return os.environ.get(f"AUTH_{key}", self.config.get(key, os.environ.get(key, default)))
    
    def _generate_key_pair(self):
        """生成 RSA 2048 密钥对"""
        tmpdir = tempfile.mkdtemp()
        try:
            priv_path = os.path.join(tmpdir, "priv.pem")
            pub_path = os.path.join(tmpdir, "pub.pem")
            subprocess.run(
                ["openssl", "genrsa", "-out", priv_path, "2048"],
                capture_output=True, check=True, timeout=10,
            )
            subprocess.run(
                ["openssl", "rsa", "-in", priv_path, "-pubout", "-out", pub_path],
                capture_output=True, check=True, timeout=10,
            )
            with open(priv_path) as f: self.priv_key = f.read()
            with open(pub_path) as f: self.pub_key = f.read()
        finally:
            for p in [priv_path, pub_path]:
                try: os.remove(p)
                except OSError: pass
            os.rmdir(tmpdir)
    
    def _rsa_encrypt_base64(self, plain_text: str, pub_key_pem: str) -> str:
        tmpdir = tempfile.mkdtemp()
        try:
            pub_path = os.path.join(tmpdir, "pub.pem")
            input_path = os.path.join(tmpdir, "input.bin")
            output_path = os.path.join(tmpdir, "output.bin")
            
            with open(pub_path, "w") as f: f.write(pub_key_pem)
            with open(input_path, "w") as f: f.write(plain_text)
            
            subprocess.run([
                "openssl", "pkeyutl", "-encrypt",
                "-inkey", pub_path, "-pubin",
                "-in", input_path, "-out", output_path,
                "-pkeyopt", "rsa_padding_mode:oaep",
                "-pkeyopt", "rsa_oaep_md:sha256",
                "-pkeyopt", "rsa_mgf1_md:sha256",
            ], capture_output=True, check=True, timeout=10)
            
            with open(output_path, "rb") as f: encrypted = f.read()
            return base64.b64encode(encrypted).decode()
        finally:
            for p in [pub_path, input_path, output_path]:
                try: os.remove(p)
                except OSError: pass
            os.rmdir(tmpdir)
    
    def _do_auth_step(self, url: str, data: bytes) -> dict:
        req = Request(url, method="POST", data=data)
        req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    
    def authenticate(self, headers: Dict[str, str]) -> Dict[str, str]:
        if not self.priv_key or not self.pub_key:
            self._generate_key_pair()
        
        # Step 1: 注册
        reg_url = f"{self.base_url}/api/dev/auth/regist"
        reg_data = urlencode({"appid": self.app_id, "cpk": self.pub_key}).encode()
        reg_result = self._do_auth_step(reg_url, reg_data)
        if not reg_result.get("status"):
            raise RuntimeError(
                f"第一步认证（注册）失败: "
                f"{reg_result.get('errmsg') or reg_result.get('msg', '未知错误')}"
            )
        secrit, spk = reg_result["secrit"], reg_result["spk"]
        self._spk = spk
        
        # Step 2: 换取 token
        token_url = f"{self.base_url}/api/dev/auth/applytoken"
        encrypted = self._rsa_encrypt_base64(secrit, spk)
        token_data = urlencode({"appid": self.app_id, "secret": encrypted}).encode()
        token_result = self._do_auth_step(token_url, token_data)
        if not token_result.get("status"):
            raise RuntimeError(
                f"第二步认证（获取 Token）失败: "
                f"{token_result.get('errmsg') or token_result.get('msg', '未知错误')}"
            )
        
        headers["token"] = token_result["token"]
        headers["appid"] = self.app_id
        return headers
