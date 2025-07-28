from typing import Any, Dict

import httpx
import structlog
from fastapi import HTTPException, status

from .config import settings

logger = structlog.get_logger()


class ServiceProxy:
    """Proxy requests to internal services"""

    def __init__(self):
        self.service_urls = {
            "auth": settings.auth_service_url,
            "data": settings.data_service_url,
            "inference": settings.inference_service_url,
        }
        self.timeout = httpx.Timeout(settings.service_timeout)

    async def forward_request(
        self,
        service: str,
        path: str,
        method: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        files: Dict[str, Any] = None,
        content: bytes = None,
    ) -> Dict[str, Any]:
        """Forward request to internal service"""

        if service not in self.service_urls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service}' not found",
            )

        service_url = self.service_urls[service]
        full_url = f"{service_url}{path}"

        # Prepare headers
        request_headers = {}
        if headers:
            # Forward specific headers
            forwarded_headers = [
                "authorization",
                "content-type",
                "user-agent",
                "x-forwarded-for",
                "x-real-ip",
            ]
            for header in forwarded_headers:
                if header in headers:
                    request_headers[header] = headers[header]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=full_url,
                    headers=request_headers,
                    params=params,
                    json=json_data,
                    files=files,
                    content=content,
                )

                # Log the request
                logger.info(
                    "Service request",
                    service=service,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds(),
                )

                # Handle different response types
                if response.status_code == 204:
                    return {"status": "success", "data": None}

                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"message": response.text}

                return {
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers),
                }

        except httpx.TimeoutException:
            logger.error(
                "Service request timeout",
                service=service,
                path=path,
                timeout=settings.service_timeout,
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service '{service}' request timed out",
            )

        except httpx.RequestError as e:
            logger.error(
                "Service request error",
                service=service,
                path=path,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Service '{service}' is unavailable",
            )

    async def health_check_service(self, service: str) -> bool:
        """Check if service is healthy"""
        if service not in self.service_urls:
            return False

        try:
            service_url = self.service_urls[service]
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                response = await client.get(f"{service_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def forward_file_request(
        self,
        service: str,
        path: str,
        method: str,
        headers: Dict[str, str] = None,
        file=None,
    ) -> Dict[str, Any]:
        """Forward file upload request to internal service"""

        if service not in self.service_urls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service '{service}' not found",
            )

        service_url = self.service_urls[service]
        full_url = f"{service_url}{path}"

        # Prepare headers (remove content-type for multipart)
        request_headers = {}
        if headers:
            forwarded_headers = [
                "authorization",
                "user-agent",
                "x-forwarded-for",
                "x-real-ip",
            ]
            for header in forwarded_headers:
                if header in headers:
                    request_headers[header] = headers[header]

        try:
            # Prepare file for forwarding
            files = {"file": (file.filename, file.file, file.content_type)}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=full_url,
                    headers=request_headers,
                    files=files,
                )

                logger.info(
                    "File upload request",
                    service=service,
                    method=method,
                    path=path,
                    filename=file.filename,
                    status_code=response.status_code,
                    response_time=response.elapsed.total_seconds(),
                )

                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"message": response.text}

                return {
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers),
                }

        except httpx.TimeoutException:
            logger.error(
                "File upload timeout",
                service=service,
                path=path,
                filename=file.filename,
                timeout=settings.service_timeout,
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"File upload to '{service}' timed out",
            )

        except httpx.RequestError as e:
            logger.error(
                "File upload error",
                service=service,
                path=path,
                filename=file.filename,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"File upload to '{service}' failed",
            )


# Global proxy instance
proxy = ServiceProxy()
