import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:ocr_suite_mobile/src/sync/shrink.dart';

void main() {
  test('large photo is downscaled to maxSide keeping the aspect ratio', () {
    final big = img.Image(width: 4000, height: 3000);
    img.fill(big, color: img.ColorRgb8(250, 250, 250));
    for (var i = 0; i < 4000; i += 7) {
      img.drawLine(big, x1: i, y1: 0, x2: 4000 - i, y2: 2999, color: img.ColorRgb8(i % 255, 40, 90));
    }
    final src = Uint8List.fromList(img.encodeJpg(big, quality: 100));
    final out = shrinkJpeg(src)!;
    final back = img.decodeJpg(out)!;
    expect(back.width, maxSide);
    expect(back.height, 1500);
    expect(out.length, lessThan(src.length));
  });

  test('undecodable bytes are left to the server', () {
    expect(shrinkJpeg(Uint8List.fromList([1, 2, 3])), isNull);
  });
}
