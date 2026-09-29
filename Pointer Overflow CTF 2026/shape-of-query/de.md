# The Shape of Query (WEB 300 / WAVE 1)

Trang: <https://pointeroverflowctf.com/challenges/shape-of-query/>
Portal: <https://shape-of-query.pointeroverflowctf.com>
Team: 612. Điểm: 300.

## Challenge Text

> Progress relies on having the right infrastructure to foster collaboration. A frictionless system for the exchange of ideas, integrity-preserving measures, and plenty of backup. There are many platforms on the market for this. Well, I'm developing my own. It's not the best. It's not the fastest. It's not the most resilient. But it is the one that I own the IP rights for, so I'm pushing it hard. Since I have a bevy of CTF player's attention, seems like a good chance to score some free pen testing. Head over to my Collaborative Research Portal and poke around a little. I am most concerned about user security. Last thing we need is for researchers to start meddling with each others' stuff.

> CONNECT
>
> The portal lives at: https://shape-of-query.pointeroverflowctf.com
>
> Present your team session token at the login screen to start a session.
>
> YOUR SESSION TOKEN
> `SHAPE1.612.81.EB7ZOZUZT7FJHWR2.<expires_unix>.<sig26>` (đã cắt chữ ký vì token hết hạn sau 15 phút)
>
> Expires in 15 minutes. Reload this page for a fresh one. Bound to your team's session; another team's token won't grant you their private notes.

> SUBMIT FLAG

## Verified Metadata

| Mục | Giá trị |
|---|---|
| Đăng nhập | `POST /session/exchange` body `{"token": "<token>"}` -> `{"ok":true,"team_id":612}` và set cookie `session` |
| API | `POST /graphql` (GraphiQL tại `/graphql`), introspection **bật** |
| Định dạng token | `SHAPE1.<team_id>.<cid>.<nonce16>.<expires_unix>.<sig26>` - nonce `EB7ZOZUZT7FJHWR2` |
| cid của bài | 81 (khớp thân flag) |
| Endpoint nộp | `POST /challenges/shape-of-query/submit`, body `{"flag":"..."}` -> `{"correct":true,"message":"Correct."}` |
| `team.members` | trả về `user_612` (MEMBER) và `admin_612` (ADMIN) - mỗi team có một tài khoản admin riêng |

Schema (nguyên văn từ introspection, xem `analysis/schema.graphql`):

```graphql
type Query { me: User   user(id: ID!): User }          # user: "You may only view yourself."
type User  { id: ID!  username: String!  role: UserRoleEnum
             team: Team  privateNotes: String }        # privateNotes: "Visible to the account owner only."
type Team  { id: ID!  name: String  members: [User] }  # members: "Cross-team enumeration is blocked."
enum UserRoleEnum { ADMIN MEMBER }
```

## Approach Summary

`user(id:)` chặn đúng (chỉ trả về chính mình, kể cả `admin_612` cùng team), nhưng **field resolver của `privateNotes` chỉ được gắn kiểm tra quyền trên đường `Query.user`, còn đường `Query.me -> Team.members -> User` thì không**. Chỉ cần đi theo shape lồng nhau là `privateNotes` của admin team mình bị trả về thô, và cờ nằm trong đó.

## Reproduce

```bash
python exploit.py "<SESSION TOKEN lấy từ trang challenge>"
```
