# Decision log - RoboCall

## H1 - tràn buffer ở các prompt
evidence: mọi input là `raw_readline(buf, len)` với `buf = rbp-0x100, len = 0x100`
(hoặc `rbp-0x200/0x200` trong cancel_plan). Vòng lặp chạy tới `count = len-1` rồi ghi NUL
tại `buf[len-1]`, tức vừa khít khung stack, byte cuối là `rbp-0x01`.
result: DEAD - không thừa byte nào. Sai lầm ban đầu: tính saved rbp nằm ở `[rbp-8]`;
nó nằm ở `[rbp]`, tức đúng sau byte cuối cùng của buffer 1 byte.
Kiểm chứng động: gửi 255 byte 'A' vào prompt cuối của payment_info, chương trình vẫn
in tiếp "Plan purchase complete" -> saved rbp không bị chạm.

## H2 - format string / số học trong switch
evidence: không có printf họ format-string (chỉ `__printf_chk` với format hằng);
mọi jump table đều bị chặn chỉ số (`cmp eax,N; ja`).
result: DEAD.

## H3 - safe-linking / tcache poison
evidence: không có malloc/calloc cấp phát động theo input -> heap không tham gia.
result: DEAD (sai thể loại).

## H4 - `raw_parse_int` không ghi `*out` trên mọi nhánh (ĐÚNG)
evidence: `14c6: cmp al,'/'; jle 14de -> mov eax,0; ret` mà không có lệnh ghi nào vào
`[rbp-0x20]` (con trỏ `out`). Các lời gọi đều truyền một biến local chưa khởi tạo,
trừ main/start_position/initial_call có `mov DWORD [rbp-0x104],0` ở đầu hàm.
cancel_plan in chính biến đó: `2f34 print "You've entered \"" ; 2f4b raw_print_int([rbp-0x204])`.
=> trả lời không phải số thì in ra 4 byte rác của stack.
result: PENDING -> xác nhận động: in ra `You've entered "0"`.

## H5 - cờ nằm ở đâu trên stack
evidence: `place_flag` mở "flag.txt", `read(fd, rbp-0x2060, 0x3c)` rồi scatter:
`dest = rbp-0x2020 + (0x19dc - CHUNK_DEPTH[i])`, 13 lần, mỗi lần 4 byte, i = 0..12.
CHUNK_DEPTH là bảng u32 tại 0x4020. place_flag return mà không in gì.
Tính theo rbp của main: chunk i nằm tại `rbp_main - (0x120 + 0x644 + CHUNK_DEPTH[i])`
= rbp_main - {0xb64,0xbe4,0xc84,0xcd4,0xd04,0xda4,0xdf4,0xe24,0xec4,0xf14,0xf44,0xf64,0xfe4}.
result: PENDING -> khớp: chunk[0] leak ra `sun{`, chunk[12] ra `tor}`.

## H6 - điều khiển độ sâu của ô leak
evidence: `rbp_callee = rbp_caller - (frame_size + 16)`, mọi frame đều là bội của 0x10,
nên độ sâu là hàm của đúng chuỗi menu đã bấm. Ô leak của cancel_plan = `rbp_cp - 0x204`.
BFS trên đồ thị menu (analysis/paths.py, cùng EDGES trong solve.py) cho ra đường đi
chạm cả 13 offset.
result: OK - 13/13.

## Ghi chú đã làm mất thời gian
1. Đọc nhầm dispatch của other_inquiries: `2ba5: je 2ca0` và `2bbc: je 2c99` là hai lệnh
   `call` kề nhau, mình đoán ngược. Thực đo: chọn 2 -> cancel_plan, chọn 3 -> operator.
2. Menu của start_position không có marker ">>>", nên chờ ">>>" là timeout.
3. Driver đếm số dòng input bị lệch một dòng (mỗi prompt in *sau* khi đọc dòng trước),
   chuyển sang đồng bộ theo marker từng prompt thì ổn.
4. `42` ở prompt đầu tắt biến global `be_annoying` -> tắt hết nanosleep, thao tác nhanh.
