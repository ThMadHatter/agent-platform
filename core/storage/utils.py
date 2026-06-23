import aiohttp
import io
from typing import BinaryIO

class StorageUtils:
    @staticmethod
    async def download_file(url: str) -> BinaryIO:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    return io.BytesIO(content)
                else:
                    raise Exception(f"Failed to download file from {url}, status: {response.status}")

class OCRProvider:
    async def perform_ocr(self, file_content: BinaryIO) -> str:
        # Placeholder for OCR logic (could use Gemini, Tesseract, or a cloud API)
        print("Performing OCR on document...")
        return "This is the extracted text from the document."
