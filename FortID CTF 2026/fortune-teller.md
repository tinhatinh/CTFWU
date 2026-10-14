---
title: "Fortune Teller"
category: "Pwn"
tags: ["format-string", "pie-leak", "targeted-overwrite"]
solve_date: "2026-10-10"
language: "vi"
---

# Fortune Teller

**Cờ trong bản ghi:** `FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}`  
**Dịch vụ:** `ncat --ssl fortune-teller-afeef2cf7bdb.inst15.ctf.fortid.com 1337` (TLS trên cổng 1337). Handout: `fortune_teller_public.zip` 4.6 KB. Tác giả: ipaljak.

## Đề bài

Dịch vụ là một `Fortune Teller`: nhận input từ người chơi rồi in ra một lời tiên tri, trong đó có một dòng blessing dựng từ một chuỗi có sẵn của chương trình. Mục tiêu là lấy cờ từ instance đang chạy.

## Phân tích

Hai dữ kiện của primitive:

1. **Đọc qua format string.** Input được đi qua một hàm in theo kiểu format string, nên `%41$p` in ra giá trị nằm ở vị trí tham số thứ 41 — trong các lần chạy của bài này, đó là một con trỏ thuộc process đang chạy. Từ leak suy ra địa chỉ chuỗi blessing có thể ghi (`bless`). Bản ghi cũng lưu một địa chỉ `ret`, nhưng chuỗi ghi đè mô tả bên dưới không sử dụng địa chỉ này.
2. **Đích ghi là chuỗi blessing.** `slot_idx=36` xác định slot chứa chuỗi blessing, và chuỗi này nằm trong vùng writable của image; ghi đè lên chính nó là đủ để đổi nội dung fortune được in ra. Không cần tới quyền thực thi mã.

Trong lần chạy được lưu, driver ghi `ret = base + 0x1664` và `bless = base + 0x404c`. `base_aligned=True` là phép kiểm tra base thẳng hàng theo trang; `bad=[]` nghĩa là không có ứng viên nào bị loại.

Ba giá trị hex trên là địa chỉ PIE của riêng lần chạy đó, sinh ra từ leak, không phải hằng số tái sử dụng được.

## Lời giải

Trình tự thực hiện trên instance, toàn bộ các bước đều chạy trực tiếp:

1. Kết nối TLS tới instance, gửi input chứa `%41$p` để đọc con trỏ lộ ra, từ đó tính base module.
2. Dùng leak để tính địa chỉ chuỗi blessing và xác nhận chỉ mục đối số format string `slot_idx=36` do driver chọn. Bản ghi không giải thích ánh xạ từ chỉ mục đối số tới thao tác ghi.
3. Dùng khả năng ghi của format string để ghi đè chuỗi blessing tại `bless`, rồi để dịch vụ in lại fortune.

Ba dòng được lưu trong record, theo đúng thứ tự của cùng một lần chạy ( `[1]` là chỉ mục lần chạy):

```text
[1] ret=0x56158039d664 base=0x56158039c000 bless=0x5615803a004c base_aligned=True bad=[] slot_idx=36
```

```text
[1] blessing says: The stars are aligned.
```

```text
FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}
```

Chuỗi trên là log của driver điều khiển phiên, không phải output nguyên văn của dịch vụ: hai dòng `[1]` là dòng do driver in ra để ghi lại giá trị suy ra được và dòng blessing mà dịch vụ trả về, còn dòng cuối là dòng cờ xuất hiện trong cùng phiên sau phép ghi đè. Record không giữ lại từng byte đã gửi ở bước 3, nên nội dung chuỗi thay thế không được trích ở đây; những gì bằng chứng cho phép nói là: đích ghi là chuỗi blessing ở slot 36, và cờ trả về trong cùng phiên sau phép ghi đó.

## Kết quả

```text
FortID{Fortun3_Fav0r5_Th3_b0ld_bu7_al50_Th05e_Th4t_C4n_Expl0i7_F0rma7_Str1ng_VulnZZ_860d534b91}
```

Bản ghi driver có chứa chuỗi cờ. Payload ghi và phần phản hồi dịch vụ xung quanh không được lưu, nên chưa thể tái hiện đầy đủ bước kích hoạt.

## Tái hiện

Cần một client TLS nói chuyện được với cổng 1337 (nmap-ncat hoặc tương đương) và một instance đang chạy:

```text
ncat --ssl fortune-teller-afeef2cf7bdb.inst15.ctf.fortid.com 1337
```

| Dữ kiện | Vai trò | Ổn định giữa các lần chạy |
|---|---|---|
| `%41$p` | token đọc con trỏ qua format string | có, là hằng số của payload |
| base module | gốc của mọi địa chỉ khác | không, PIE, phải lấy từ leak |
| `base + 0x1664` | vị trí `ret` trong log lần chạy được ghi lại | chưa được kiểm chứng qua nhiều bản |
| `base + 0x404c` | địa chỉ chuỗi blessing (`bless`) | chưa được kiểm chứng qua nhiều bản |
| `slot_idx=36` | slot chứa chuỗi blessing writable | slot được dịch vụ báo lại qua leak |

Hai offset `0x1664` và `0x404c` lấy từ một lần chạy đã lưu, chưa được kiểm tra trên instance khác. Script điều khiển phiên và payload ghi bị thiếu. Bản ghi cho thấy một lần leak pointer và một output có cờ, nhưng chưa đủ dữ liệu để tái hiện phép ghi đè hoặc xác nhận chuỗi blessing là trigger. Bài viết không nêu mitigation của binary vì các bằng chứng đã lưu không có dữ liệu kiểm tra mitigation.
