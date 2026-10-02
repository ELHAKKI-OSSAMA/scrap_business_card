import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:image/image.dart' as img;

/// Serverless hosts cap request bodies (Vercel: 4.5 MB) and the OCR model reads ≤1600 px, so
/// photos above [resizeAboveBytes] are downscaled to [maxSide] px (JPEG) before upload.
/// The draft keeps the original; only the uploaded copy is smaller.
const int resizeAboveBytes = 2621440; // 2.5 MB
const int maxSide = 2000;

Future<File> shrinkForUpload(File file) async {
  if (await file.length() <= resizeAboveBytes) return file;
  final out = await compute(shrinkJpeg, await file.readAsBytes());
  if (out == null) return file; // undecodable here: let the server validate and answer
  final tmp = File('${file.path}.upload.jpg');
  await tmp.writeAsBytes(out, flush: true);
  return tmp;
}

/// Pure function (runs in an isolate). Applies EXIF orientation, keeps the aspect ratio.
Uint8List? shrinkJpeg(Uint8List bytes) {
  img.Image? decoded;
  try {
    decoded = img.decodeImage(bytes);
  } catch (_) {
    return null; // corrupt / unsupported: the server validates and answers
  }
  if (decoded == null) return null;
  var im = img.bakeOrientation(decoded);
  final longest = im.width > im.height ? im.width : im.height;
  if (longest > maxSide) {
    im = im.width >= im.height ? img.copyResize(im, width: maxSide) : img.copyResize(im, height: maxSide);
  }
  final jpg = img.encodeJpg(im, quality: 88);
  return jpg.length < bytes.length ? jpg : null;
}
