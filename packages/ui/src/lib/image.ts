/** Downscale large photos in the browser before upload.
 * Serverless hosts cap request bodies (Vercel: 4.5 MB) and the OCR model works on ≤1600 px anyway.
 * Small files are sent untouched; EXIF orientation is applied by the browser when decoding. */
export const MAX_UPLOAD_SIDE = 2000;
export const RESIZE_ABOVE_BYTES = 2.5 * 1024 * 1024;

export async function shrinkForUpload(file: File): Promise<File> {
  if (file.size <= RESIZE_ABOVE_BYTES || typeof createImageBitmap !== "function") return file;
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, MAX_UPLOAD_SIDE / Math.max(bmp.width, bmp.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bmp.width * scale);
    canvas.height = Math.round(bmp.height * scale);
    canvas.getContext("2d")?.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    bmp.close();
    const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, "image/jpeg", 0.9));
    if (!blob || blob.size >= file.size) return file;
    return new File([blob], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" });
  } catch {
    return file; // the server still validates and rejects what it cannot read
  }
}
