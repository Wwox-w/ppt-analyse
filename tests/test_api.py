"""API 接口测试"""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealthAPI:
    """测试健康检查接口"""

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ppt-analyse"


class TestUploadAPI:
    """测试文件上传接口"""

    def test_upload_invalid_file(self):
        """测试上传不支持的文件格式"""
        response = client.post(
            "/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 400
        assert "仅支持" in response.json()["detail"]
