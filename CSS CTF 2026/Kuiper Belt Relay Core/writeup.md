# Kuiper Belt Relay Core - Pwn (Beginner)

**Sự kiện:** CSS CTF 2026  
**Phân loại:** pwn  
**Mức độ:** Beginner (50 điểm)

## Đề bài

Hệ thống cung cấp một dịch vụ phản hồi chuỗi (echo service) hoạt động dựa trên hàm `vuln()`. Hàm này tiếp nhận dữ liệu đầu vào thông qua lời gọi hàm không an toàn `gets(buffer[64])`. Một hàm có tên `win()` đã được khai báo sẵn trong mã nguồn nhưng không có đường dẫn thực thi hợp lệ (dead code). Mục tiêu của thử thách: Lợi dụng lỗ hổng tràn bộ đệm (buffer overflow) tại `gets` để ghi đè địa chỉ trả về (return address), từ đó điều hướng luồng điều khiển của chương trình nhảy trực tiếp vào hàm `win()` nhằm xuất cờ (flag).

Mã nguồn đính kèm:
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win() {
    printf("\nYou hijacked the return address!\n");
    printf("Here's your flag:\n");
    FILE *f = fopen("flag.txt", "r");
    if (f == NULL) {
        printf("Error: flag.txt not found on server.\n");
        exit(1);
    }
    char flag[128];
    if (fgets(flag, sizeof(flag), f)) {
        printf("%s\n", flag);
    }
    fclose(f);
    exit(0);
}

void vuln() {
    char buffer[64];
    printf("This program is a simple echo service.\n");
    printf("Enter your message: ");
    gets(buffer);
    printf("You said: %s\n", buffer);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    printf("Goodbye!\n");
    return 0;
}
```

## Phân tích ban đầu

- Đặc tả vùng nhớ bộ đệm: Mảng `char buffer[64]` được phân bổ bắt đầu tại mức chênh lệch (offset) 0 trên khung ngăn xếp (stack frame) của hàm `vuln`.
- Kỹ thuật xác định ranh giới tràn bộ đệm thông qua tương tác ngoại vi (Black-box testing): Khi truyền payload gồm chuỗi `"A"*71`, chương trình vẫn hoạt động ổn định và in ra thông báo `Goodbye!`. Tuy nhiên, với payload `"A"*72`, thông báo này không còn xuất hiện, xác nhận chương trình đã gặp lỗi phân đoạn (crash) trước khi lệnh in cuối cùng trong hàm `main` được thực thi.
- Dựa trên kết quả này, hệ thống khẳng định địa chỉ trả về (return address) nằm tại **offset 72** (Bao gồm 64 byte dành cho bộ đệm và 8 byte cho thanh ghi Base Pointer - saved RBP).
- Tệp nhị phân được biên dịch tương thích kiến trúc x86-64 và không kích hoạt cơ chế PIE (Position Independent Executable). Việc rà quét các địa chỉ tĩnh thành công và xác nhận toàn bộ phân vùng nằm trong dải `0x40xxxx`.

## Các hướng đã loại trừ

### Rò rỉ thông tin bộ nhớ ngăn xếp (Stack Leak) thông qua lỗi chuỗi định dạng (Format String)

- Phép thử: Truyền payload định dạng `b"A"*n + b"%s%s%s..."` với chủ đích đọc xuất các giá trị nằm trên ngăn xếp liền kề sau vùng đệm.
- Kết quả: Không thu hồi được bất kỳ giá trị địa chỉ khả dụng nào. Đào sâu phân tích kiến trúc hàm `gets()`, hàm này tự động chèn một ký tự kết thúc chuỗi `\x00` (NUL terminator) ngay sau khối dữ liệu đầu vào. Do hệ thống 64-bit sử dụng địa chỉ bắt đầu bằng byte `0x40` và áp dụng định dạng Little-Endian, byte thấp nhất (Least Significant Byte - LSB, ví dụ `0x16`) sẽ được nạp đầu tiên. Việc chèn ký tự `\x00` vô tình đè lên chính byte thấp của địa chỉ trả về, dẫn đến chuỗi định dạng bị ngắt kết nối ngay lập tức, vô hiệu hóa hoàn toàn hiệu lực của kỹ thuật rò rỉ bộ nhớ.
- Kết luận: Buộc phải loại bỏ phương án sử dụng lỗi chuỗi định dạng để dò tìm địa chỉ hàm `win()`. Phương án tối ưu thay thế là kỹ thuật dò quét trực tiếp dựa trên phản hồi hệ thống (oracle-based scanning).

## Chuỗi khai thác

**Bước 1 - Định vị chính xác ranh giới của địa chỉ trả về.**

Truyền lần lượt các payload có kích thước tịnh tiến và giám sát phản hồi máy chủ để tìm ngưỡng phá vỡ quy trình in chuỗi `Goodbye!`:

```text
Chuỗi "A"*64 → Trạng thái bình thường, phản hồi chứa "Goodbye!"
Chuỗi "A"*71 → Trạng thái bình thường, phản hồi chứa "Goodbye!"
Chuỗi "A"*72 → Trạng thái bất thường, chỉ phản hồi ký tự ngắt dòng (Mất "Goodbye!")
```

Cơ sở này củng cố kết luận return address bắt đầu ở giới hạn byte thứ 72.

**Bước 2 - Quét rà phản hồi (Oracle-based scanning) để trích xuất địa chỉ hàm `win()`.**

Trong điều kiện không có file thực thi cục bộ để trích xuất danh mục địa chỉ tĩnh, quy trình dò quét bắt buộc tiến hành trực tiếp đối với máy chủ trong phạm vi phân đoạn mã `.text` (Kéo dài từ `0x401000` đến `0x401500`).

- Cấu trúc Payload cho mỗi bước thử nghiệm: `b"A"*72 + low_bytes(addr)` (Định dạng Little-Endian, bảo đảm an toàn khi ký tự NUL kết thúc chuỗi).
- Dấu hiệu phân biệt (Oracle): Dựa trên việc phân tích phản hồi máy chủ có chứa chuỗi "hijacked" hoặc "CSSCTF" hay không.

Kết quả quét tự động phát hiện hàm `win()` tồn tại tại địa chỉ: **0x401216**.

**Bước 3 - Kiến trúc Payload khai thác (Exploit Payload).**

Bởi địa chỉ `0x401216` nhỏ hơn ngưỡng `0x1000000`, hệ thống chỉ yêu cầu ghi đè 3 byte thấp nhất: `0x16 0x12 0x40`.

Cấu trúc Payload hoàn thiện: `b"A"*72 + b"\x16\x12\x40"`.

**Bước 4 - Thử nghiệm thực tiễn (Kiểm chứng).**

Triển khai Payload lên máy chủ mục tiêu trong 3 phiên độc lập. Cả 3 phiên đều vượt qua hàng rào bảo vệ, chiếm quyền điều khiển và trả về cờ thành công.

## Flag

Kết quả:
```text
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Reproduce

Quá trình tự động tái thiết lập bằng công cụ (script):

```bash
python exploit.py
```

Đầu ra hệ thống:
```text
This program is a simple echo service.
Enter your message: You hijacked the return address!
Here's your flag:
CSSCTF{s1gn4l_r3c0v3r3d_fr0m_th3_v01d}
```

## Tài liệu đính kèm (Files)

- **exploit.py**: Mã kịch bản điều phối khai thác tự động.
- **de.png**: Ảnh màn hình chứa nội dung đề bài gốc.
- **analysis/**: Tập hợp các script hỗ trợ quá trình quét dò và phân tích giai đoạn.
