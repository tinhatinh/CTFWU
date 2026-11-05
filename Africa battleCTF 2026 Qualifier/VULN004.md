---
title: "VULN#004"
category: "Vuln Research"
tags: ["giflib", "gif", "double-free", "reallocarray", "thumbnail-service", "crash-oracle"]
solve_date: "2026-10-27T06:25:05+07:00"
language: "vi"
points: 148
---

# VULN#004 — giflib double-free khi image counter về 0

**Flag:** CTF{2637c464bb603890315dd4f99714c6ea}  
**Service:** 169.58.126.107:7029  
**Định dạng flag:** CTF{}

## Đề bài

> VULN#004 — 148 điểm. Thumbnail service decode mọi GIF được gửi tới. Có source tree chính xác dùng để build target binary.

Service nhận length big-endian 4 byte rồi số raw bytes tương ứng. Harness mở GIF, gọi DGifSlurp(), đóng file, rồi báo process có crash hay không. Target là dịch vụ thumbnail “Ghost-Pixel”; source là giflib 5.2.2.

## Phân tích

### Bug

giflib 5.2.2 gọi DGifDecreaseImageCounter() trong đường xử lý lỗi khi image decode thất bại. Function giảm ImageCount, free raster của image lỗi rồi thu nhỏ mảng SavedImages:

```c
void DGifDecreaseImageCounter(GifFileType *GifFile) {
    GifFile->ImageCount--;
    if (GifFile->SavedImages[GifFile->ImageCount].RasterBits != NULL) {
        free(GifFile->SavedImages[GifFile->ImageCount].RasterBits);
    }

    // Realloc array according to the new image counter.
    SavedImage *correct_saved_images = (SavedImage *)reallocarray(
        GifFile->SavedImages, GifFile->ImageCount, sizeof(SavedImage));
    if (correct_saved_images != NULL) {
        GifFile->SavedImages = correct_saved_images;
    }
}
```

Nếu image lỗi là image đầu tiên, ImageCount thành 0 và hàm gọi reallocarray(ptr, 0, sizeof(SavedImage)). Trên glibc, reallocarray(ptr, 0, size) tương tự realloc(ptr, 0): giải phóng ptr và trả NULL. Vì kết quả NULL, code giữ GifFile->SavedImages trỏ tới vùng đã free. Sau đó DGifCloseFile() free SavedImages lần nữa — double-free.

Upstream fix là commit c2585d0 (2026-04-11, “Avoid a dodgy edge case in reallocarray()”, SourceForge bug #193):

```c
if (GifFile->ImageCount <= 0) {
    free(GifFile->SavedImages);
    GifFile->SavedImages = NULL;
    GifFile->ImageCount = 0;
    return;
}
```

Một chi tiết quyết định hộp có crash hay không: openbsd_reallocarray() đi kèm trả NULL khi count 0 nhưng không free; build dùng implementation này sẽ không double-free. Target dùng reallocarray của hệ thống (HAVE_REALLOCARRAY), vốn có free.

### Pre-validator

Service từ chối GIF thiếu cấu trúc trước khi tới giflib:

- Image descriptor có width bằng 0;
- Image không có data block;
- Pixel data hoàn chỉnh nhưng thiếu 0x00 block terminator hoặc 0x3B trailer.

Các trường hợp đó đều trả status: not valid. PoC cần GIF hợp lệ về cấu trúc nhưng vẫn làm DGifSlurp() lỗi trong lúc giải mã raster.

## PoC

File hoạt động là GIF89a dài 86,906 byte, gồm:

| Thuộc tính | Giá trị |
|---|---|
| Logical screen / GCT | GIF89a header và global colour table hợp lệ |
| Image descriptor | 4096 × 57585 — 235,868,160 pixel |
| LZW data | sub-block chain đầy đủ với 16 growth-chain cycle (~117,934,080 pixel) |
| Kết thúc | 0x00 block terminator và 0x3B trailer hợp lệ |

LZW stream chỉ lấp khoảng nửa raster đã khai báo. Validator thấy cấu trúc đầy đủ, nhưng DGifSlurp() giải mã khoảng 118 triệu pixel rồi gặp terminator sớm (Error=112, ImageCount từ 1 về 0) và gọi DGifDecreaseImageCounter().

Tham chiếu PoC (dựng lại từ phiên solve):

```text
poc_slow_invalid.gif
86,906 bytes
sha256 163f02c485e0e1f2c5722e509dfae126bb6e94afb69707778c7af4223695f17c
```

Xác nhận local trên bản build còn lỗi (-DHAVE_REALLOCARRAY):

```text
DGifSlurp returned 0 ..., ImageCount=0, Error=112
free(): double free detected in tcache 2   (SIGABRT)
```

ASAN xác định lần free thứ hai đến từ GifFreeSavedImages() được gọi qua DGifCloseFile(). Bản Makefile mặc định dùng openbsd_reallocarray đi kèm và **không** crash — vì vậy ban đầu lỗi có vẻ như không tồn tại.

### Gửi PoC

```python
import socket, struct

data = open("poc_slow_invalid.gif", "rb").read()
s = socket.create_connection(("169.58.126.107", 7029), timeout=10)
s.sendall(struct.pack(">I", len(data)) + data)
print(s.recv(4096).decode())
```
```text
status: crash confirmed (double-free in giflib decode cleanup)
FLAG: CTF{2637c464bb603890315dd4f99714c6ea}
```

## Ghi chú

- Target phân biệt crash mục tiêu với crash khác. Trigger cũ (image width 0, thiếu terminator, thiếu data block) bị structural validator trả not valid nên chưa chạy qua giflib error path.
- Điều kiện quan trọng là **cấu trúc đầy đủ nhưng raster chưa đủ**: đủ để qua validator nhưng decode lỗi ở image đầu tiên, làm counter về 0.
- Service hoạt động như crash oracle; packet thành công trả target signature và flag.

## Tham khảo

- giflib 5.2.2 dgif_lib.c
- giflib commit c2585d037fb619aa2df06dc8ba44bf894bcfdba2 — “Avoid a dodgy edge case in reallocarray()”
- SourceForge bug #193 — double-free trong DGifDecreaseImageCounter khi ImageCount về 0
