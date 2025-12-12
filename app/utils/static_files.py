"""
Custom static files handler with caching support
"""
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope, Receive, Send
import os
import mimetypes


class CachedStaticFiles(StaticFiles):
    """
    Static files handler that adds Cache-Control headers for better performance.
    
    This class extends FastAPI's StaticFiles to automatically add appropriate
    cache headers for static assets like images, CSS, and JavaScript files.
    """
    
    def __init__(
        self,
        *,
        directory: str = None,
        packages: list = None,
        html: bool = False,
        check_dir: bool = True,
        cache_max_age: int = 31536000,  # 1 year in seconds
    ) -> None:
        """
        Initialize CachedStaticFiles.
        
        Args:
            directory: Path to the directory containing static files
            packages: List of package names to serve static files from
            html: Whether to serve HTML files
            check_dir: Whether to check if directory exists
            cache_max_age: Maximum age for cache in seconds (default: 1 year)
        """
        super().__init__(
            directory=directory,
            packages=packages,
            html=html,
            check_dir=check_dir
        )
        self.cache_max_age = cache_max_age
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle request and add cache headers.
        """
        if scope["type"] == "http":
            # Get the original send function
            original_send = send
            
            async def send_with_cache_headers(message):
                """Add cache headers to response"""
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    
                    # Get the file path from the request
                    path = scope.get("path", "")
                    
                    # Determine cache duration based on file type
                    cache_duration = self._get_cache_duration(path)
                    
                    # Add Cache-Control header
                    cache_control = f"public, max-age={cache_duration}, immutable"
                    headers.append((b"cache-control", cache_control.encode()))
                    
                    # Add additional headers for better caching
                    # ETag is handled by StaticFiles automatically
                    
                    message["headers"] = headers
                
                await original_send(message)
            
            # Call parent with modified send function
            await super().__call__(scope, receive, send_with_cache_headers)
        else:
            await super().__call__(scope, receive, send)
    
    def _get_cache_duration(self, path: str) -> int:
        """
        Get appropriate cache duration based on file type.
        
        Args:
            path: The file path
            
        Returns:
            Cache duration in seconds
        """
        # Get file extension
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        # Define cache durations for different file types
        # Images: 1 year (they rarely change and are versioned by filename)
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.svg', '.ico']:
            return 31536000  # 1 year
        
        # CSS and JS: 1 year (should be versioned)
        elif ext in ['.css', '.js']:
            return 31536000  # 1 year
        
        # Fonts: 1 year
        elif ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
            return 31536000  # 1 year
        
        # Videos: 1 month
        elif ext in ['.mp4', '.webm', '.ogg']:
            return 2592000  # 30 days
        
        # PDFs and documents: 1 week
        elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
            return 604800  # 7 days
        
        # Default: use the configured max age
        return self.cache_max_age


class MediaStaticFiles(CachedStaticFiles):
    """
    Specialized static files handler for media uploads with optimized cache settings.
    """
    
    def __init__(
        self,
        *,
        directory: str = None,
        packages: list = None,
        html: bool = False,
        check_dir: bool = True,
    ) -> None:
        """
        Initialize MediaStaticFiles with optimized settings for media files.
        """
        # Media files (images, videos) benefit from longer cache times
        super().__init__(
            directory=directory,
            packages=packages,
            html=html,
            check_dir=check_dir,
            cache_max_age=31536000,  # 1 year
        )
